const express = require('express');
const mongoose = require('mongoose');

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/sportsbooks');

const db = mongoose.connection;
db.on('error', console.error.bind(console, 'connection error:'));
db.once('open', () => {
    console.log('Connected to MongoDB');
});

// Define schema and model for DraftKings
const dkSchema = new mongoose.Schema({
    Away: String,
    Home: String,
    HSPR: {
        draftkings: String
    },
    HSPRO: {
        draftkings: String
    },
    ASPR: {
        draftkings: String
    },
    ASPRO: {
        draftkings: String
    },
    "O/U": {
        draftkings: String
    },
    AML: {
        draftkings: String
    },
    HML: {
        draftkings: String
    }
});

const DKOdds = mongoose.model('DKOdds', dkSchema, 'dk_nfl_odds');

// Define schema and model for ESPNBet
const espnSchema = new mongoose.Schema({
    Away: String,
    Home: String,
    HSPR: {
        espnbet: String
    },
    HSPRO: {
        espnbet: String
    },
    ASPR: {
        espnbet: String
    },
    ASPRO: {
        espnbet: String
    },
    "O/U": {
        espnbet: String
    },
    AML: {
        espnbet: String
    },
    HML: {
        espnbet: String
    }
});

const ESPNOdds = mongoose.model('ESPNOdds', espnSchema, 'espn_nfl_odds');

// Function to merge odds data
// Function to merge odds data
const mergeOddsData = (dkData, espnData) => {
    const mergedData = [];

    const espnMap = espnData.reduce((acc, game) => {
        const key = `${game.Away} @ ${game.Home}`;
        acc[key] = game;
        return acc;
    }, {});

    for (const dkGame of dkData) {
        const key = `${dkGame.Away} @ ${dkGame.Home}`;
        const espnGame = espnMap[key];

        if (espnGame) {
            const mergedGame = {
                Away: dkGame.Away,
                Home: dkGame.Home,
                HSPR: {
                    draftkings: dkGame.HSPR.draftkings,
                    espnbet: espnGame.HSPR.espnbet
                },
                HSPRO: {
                    draftkings: dkGame.HSPRO.draftkings,
                    espnbet: espnGame.HSPRO.espnbet
                },
                ASPR: {
                    draftkings: dkGame.ASPR.draftkings,
                    espnbet: espnGame.ASPR.espnbet
                },
                ASPRO: {
                    draftkings: dkGame.ASPRO.draftkings,
                    espnbet: espnGame.ASPRO.espnbet
                },
                "O/U": {
                    draftkings: dkGame["O/U"].draftkings,
                    espnbet: espnGame["O/U"].espnbet
                },
                AML: {
                    draftkings: dkGame.AML.draftkings,
                    espnbet: espnGame.AML.espnbet
                },
                HML: {
                    draftkings: dkGame.HML.draftkings,
                    espnbet: espnGame.HML.espnbet
                }
            };

            mergedData.push(mergedGame);
        }
    }

    return mergedData;
};


// Route to get combined odds data
app.get('/api/odds', async (req, res) => {
    try {
        const dkOdds = await DKOdds.find();
        const espnOdds = await ESPNOdds.find();
        const combinedOdds = mergeOddsData(dkOdds, espnOdds);
        res.json(combinedOdds);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});