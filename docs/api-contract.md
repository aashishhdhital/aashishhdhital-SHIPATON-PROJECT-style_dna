# StyleDNA API Contract

Base URL during local development:

http://127.0.0.1:8000

---

## 1. Health Check

### GET /health

Response:

{
  "status": "ok"
}

---

## 2. Analyze Style

### POST /style/analyze

Purpose:

Analyze the user's selected fashion inspiration images and generate a Style DNA profile.

Request type:

multipart/form-data

Fields:

- user_id
- images[]

Example response:

{
  "profile_id": 1,
  "styles": [
    {
      "name": "minimalist",
      "score": 40
    },
    {
      "name": "streetwear",
      "score": 35
    }
  ],
  "colors": [
    "black",
    "white",
    "beige"
  ],
  "garments": [
    "oversized shirt",
    "wide-leg trousers"
  ],
  "traits": [
    "neutral palette",
    "relaxed fit"
  ]
}

---

## 3. Generate Outfit

### POST /outfits/generate

Request:

{
  "user_id": 1,
  "occasion": "college"
}

Response:

{
  "id": 1,
  "occasion": "college",
  "match_score": 92,
  "items": [
    {
      "category": "top",
      "description": "Oversized black t-shirt"
    },
    {
      "category": "bottom",
      "description": "Relaxed beige trousers"
    },
    {
      "category": "shoes",
      "description": "White sneakers"
    }
  ],
  "reason": "Matches the user's minimalist and streetwear preferences."
}

---

## 4. Get Profile

### GET /profile/{user_id}

Response:

{
  "id": 1,
  "name": "Demo User",
  "style_profile": {
    "styles": [
      {
        "name": "minimalist",
        "score": 40
      }
    ],
    "colors": [
      "black",
      "white",
      "beige"
    ]
  }
}

---

## 5. Outfit Feedback

### POST /outfits/{outfit_id}/feedback

Request:

{
  "reaction": "like"
}

Allowed values:

- like
- maybe
- dislike

Response:

{
  "status": "saved"
}