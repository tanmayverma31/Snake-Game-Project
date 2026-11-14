-- ====================================================================
-- Snake Game Backend - High Score & Match Persistence Schema (SQLite)
-- ====================================================================

CREATE TABLE IF NOT EXISTS high_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD', 'EXPERT', 'CUSTOM')),
    foods_eaten INTEGER NOT NULL DEFAULT 0 CHECK (foods_eaten >= 0),
    duration_seconds REAL NOT NULL DEFAULT 0.0 CHECK (duration_seconds >= 0.0),
    grid_size TEXT NOT NULL DEFAULT '20x20',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast leaderboard lookups filtered by difficulty and ordered by highest score
CREATE INDEX IF NOT EXISTS idx_high_scores_difficulty_score 
ON high_scores (difficulty, score DESC, duration_seconds ASC);

-- Index for player history / player best queries
CREATE INDEX IF NOT EXISTS idx_high_scores_player 
ON high_scores (player_name, score DESC);
