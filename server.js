const express = require('express');
const http = require('http');
const socketIO = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIO(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// تخزين الغرف: roomId -> { player1: socketId, player2: socketId, gameState }
const rooms = new Map();

function generateRandomTarget() {
    return Math.random() * 8 + 3; // 3.0 إلى 11.0
}

function getDefaultGameState() {
    return {
        players: [
            { score: 0, attempt: null, hasPlayed: false },
            { score: 0, attempt: null, hasPlayed: false }
        ],
        currentTurn: 0,
        targetTime: generateRandomTarget(),
        roundActive: true,
        timerRunning: false,
        elapsed: 0
    };
}

function broadcastGameState(roomId) {
    const room = rooms.get(roomId);
    if (!room) return;
    const state = room.gameState;
    io.to(room.player1).to(room.player2).emit('game-state', {
        players: state.players,
        currentTurn: state.currentTurn,
        targetTime: state.targetTime,
        roundActive: state.roundActive,
        timerRunning: state.timerRunning,
        elapsed: state.elapsed
    });
}

function endRound(roomId) {
    const room = rooms.get(roomId);
    if (!room) return;
    const state = room.gameState;
    if (!state.roundActive) return;
    state.roundActive = false;
    state.timerRunning = false;
    const diff1 = Math.abs(state.players[0].attempt - state.targetTime);
    const diff2 = Math.abs(state.players[1].attempt - state.targetTime);
    let winner = null;
    if (diff1 < diff2) {
        state.players[0].score++;
        winner = 'player1';
    } else if (diff2 < diff1) {
        state.players[1].score++;
        winner = 'player2';
    }
    broadcastGameState(roomId);
    io.to(room.player1).to(room.player2).emit('round-ended', {
        winner,
        scores: [state.players[0].score, state.players[1].score]
    });
}

function resetRound(roomId) {
    const room = rooms.get(roomId);
    if (!room) return;
    const state = room.gameState;
    state.players[0].attempt = null;
    state.players[0].hasPlayed = false;
    state.players[1].attempt = null;
    state.players[1].hasPlayed = false;
    state.currentTurn = 0;
    state.roundActive = true;
    state.timerRunning = false;
    state.elapsed = 0;
    broadcastGameState(roomId);
}

function newRound(roomId) {
    const room = rooms.get(roomId);
    if (!room) return;
    const state = room.gameState;
    state.players[0].attempt = null;
    state.players[0].hasPlayed = false;
    state.players[1].attempt = null;
    state.players[1].hasPlayed = false;
    state.currentTurn = 0;
    state.roundActive = true;
    state.timerRunning = false;
    state.elapsed = 0;
    state.targetTime = generateRandomTarget();
    broadcastGameState(roomId);
    io.to(room.player1).to(room.player2).emit('new-round', { targetTime: state.targetTime });
}

io.on('connection', (socket) => {
    console.log(`New client: ${socket.id}`);

    socket.on('create-room', ({ roomId }) => {
        if (rooms.has(roomId)) {
            socket.emit('error', { message: 'الغرفة موجودة بالفعل، اختر اسماً آخر' });
            return;
        }
        const gameState = getDefaultGameState();
        rooms.set(roomId, {
            player1: socket.id,
            player2: null,
            gameState
        });
        socket.join(roomId);
        socket.emit('room-created', { roomId });
        console.log(`Room ${roomId} created by ${socket.id}`);
    });

    socket.on('join-room', ({ roomId }) => {
        const room = rooms.get(roomId);
        if (!room) {
            socket.emit('error', { message: 'الغرفة غير موجودة' });
            return;
        }
        if (room.player1 && room.player2) {
            socket.emit('error', { message: 'الغرفة ممتلئة' });
            return;
        }
        let playerId = 'player2';
        if (!room.player1) {
            room.player1 = socket.id;
            playerId = 'player1';
        } else {
            room.player2 = socket.id;
            playerId = 'player2';
        }
        socket.join(roomId);
        socket.emit('room-joined', { roomId, playerId });
        if (room.player1 && room.player2) {
            broadcastGameState(roomId);
        }
        console.log(`${socket.id} joined room ${roomId} as ${playerId}`);
    });

    socket.on('start-timer', ({ roomId }) => {
        const room = rooms.get(roomId);
        if (!room) return;
        const state = room.gameState;
        const currentPlayerSocket = state.currentTurn === 0 ? room.player1 : room.player2;
        if (socket.id !== currentPlayerSocket) {
            socket.emit('action-ack', { success: false, message: 'ليس دورك' });
            return;
        }
        if (state.players[state.currentTurn].hasPlayed) {
            socket.emit('action-ack', { success: false, message: 'لقد لعبت بالفعل' });
            return;
        }
        if (state.timerRunning) {
            socket.emit('action-ack', { success: false, message: 'التايمر يعمل بالفعل' });
            return;
        }
        state.timerRunning = true;
        state.elapsed = 0;
        broadcastGameState(roomId);
        socket.emit('action-ack', { success: true });
    });

    socket.on('stop-timer', ({ roomId, stopTime }) => {
        const room = rooms.get(roomId);
        if (!room) return;
        const state = room.gameState;
        const currentPlayerSocket = state.currentTurn === 0 ? room.player1 : room.player2;
        if (socket.id !== currentPlayerSocket) {
            socket.emit('action-ack', { success: false, message: 'ليس دورك' });
            return;
        }
        if (!state.timerRunning) {
            socket.emit('action-ack', { success: false, message: 'التايمر لا يعمل' });
            return;
        }
        state.timerRunning = false;
        state.players[state.currentTurn].attempt = stopTime;
        state.players[state.currentTurn].hasPlayed = true;
        broadcastGameState(roomId);
        if (state.players[0].hasPlayed && state.players[1].hasPlayed) {
            endRound(roomId);
        } else {
            state.currentTurn = state.currentTurn === 0 ? 1 : 0;
            broadcastGameState(roomId);
        }
        socket.emit('action-ack', { success: true });
    });

    socket.on('reset-round', ({ roomId }) => {
        const room = rooms.get(roomId);
        if (!room) return;
        resetRound(roomId);
    });

    socket.on('next-round', ({ roomId }) => {
        const room = rooms.get(roomId);
        if (!room) return;
        newRound(roomId);
    });

    socket.on('disconnect', () => {
        // حذف الغرفة إذا انقطع أحد اللاعبين
        for (let [roomId, room] of rooms.entries()) {
            if (room.player1 === socket.id || room.player2 === socket.id) {
                io.to(roomId).emit('error', { message: 'انقطع أحد اللاعبين، يتم إغلاق الغرفة' });
                rooms.delete(roomId);
                console.log(`Room ${roomId} deleted due to disconnect`);
                break;
            }
        }
        console.log(`Client disconnected: ${socket.id}`);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
