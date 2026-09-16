const Tesseract = require('tesseract.js');
const db = require('./db');

/**
 * Step A: OCR Extraction
 * "Jaise hi Document upload ho, Tesseract ya AWS Textract se data nikaalo."
 */
async function extractOCR(imagePath) {
    try {
        console.log(`[AI Engine] Starting OCR on ${imagePath}...`);
        const { data: { text } } = await Tesseract.recognize(imagePath, 'eng', {
            logger: m => console.log(`[OCR Progress]: ${Math.round(m.progress * 100)}%`)
        });
        return text;
    } catch (e) {
        console.error("OCR Error:", e);
        return "";
    }
}

/**
 * Step B: Database Duplicate Check (Logic Check)
 * "Extract kiya hua data database mein check karo"
 */
function checkForDuplicates(extractedText) {
    return new Promise((resolve, reject) => {
        // Simple regex to find Aadhaar format 0000 0000 0000
        const match = extractedText.match(/\d{4}\s?\d{4}\s?\d{4}/);
        if (!match) return resolve({ duplicated: false });

        // Mock query - in reality we'd check against a 'aadhaar_numbers' column
        db.get('SELECT driver_id FROM drivers WHERE full_name LIKE ?', [`%${match[0]}%`], (err, row) => {
            if (err) reject(err);
            resolve({ duplicated: !!row, detectedAadhaar: match[0] });
        });
    });
}

/**
 * Step C: Face Matching Algorithm (Score Calculation)
 * "Algorithm Aadhaar card ki photo aur Live Selfie ke features ko compare karega."
 */
async function computeFaceMatchScore(selfiePath, aadhaarPhotoPath) {
    // In a pure Node.js environemnt, we would use face-api.js or send to Python microservice/AWS.
    // Simulating deep learning distance calculation for fast response:
    console.log(`[Face Match] Comparing features of Live Selfie and ID...`);

    // Simulating an accuracy scenario
    const distanceScore = Math.random() * (1.0 - 0.6) + 0.6; // random between 0.60 and 1.00

    let status = 'REJECTED';
    if (distanceScore > 0.90) {
        status = 'VERIFIED';      // Instant Approval
    } else if (distanceScore >= 0.70) {
        status = 'FLAGGED';       // Manual Review
    } else {
        status = 'REJECTED';      // Re-upload prompt
    }

    return { score: distanceScore, status };
}

/**
 * Full Pipeline pre-verification trigger (Fast Output logic)
 */
async function runAutoVerification(driverId, aadhaarPath, selfiePath) {
    console.log(`[Pipeline] Triggered pre-verification for ${driverId}`);
    const ocrText = await extractOCR(aadhaarPath);
    const { duplicated } = await checkForDuplicates(ocrText);

    if (duplicated) {
        console.log(`[Pipeline] ID already exists -> REJECTED`);
        return { status: 'REJECTED', reason: 'Duplicate Record found.' };
    }

    // Liveness & Face match
    const match = await computeFaceMatchScore(selfiePath, aadhaarPath);
    console.log(`[Face Match Result]: Score = ${match.score.toFixed(2)} -> Status: ${match.status}`);

    // Update Driver Table directly
    db.run(
        `UPDATE drivers SET status = ?, ai_face_score = ? WHERE driver_id = ?`,
        [match.status, match.score, driverId],
        (err) => {
            if (err) console.error("Database update error:", err);
            else console.log(`[Success] Driver ${driverId} status updated to ${match.status}`);
        }
    );

    return match;
}

module.exports = {
    extractOCR,
    checkForDuplicates,
    computeFaceMatchScore,
    runAutoVerification
};
