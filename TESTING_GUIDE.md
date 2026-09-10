# Testing Guide: AI Question Generation

## Prerequisites

1. **Backend API Running**
   ```bash
   cd edukoreaiapi
   source .venv/Scripts/activate  # or .venv\Scripts\activate on Windows
   python main.py
   # Should start on http://0.0.0.0:8000
   ```

2. **UI Running**
   ```bash
   cd edukoreaiui
   source .venv/Scripts/activate
   python main.py
   ```

3. **MongoDB Running**
   - Default: mongodb://localhost:27017/

4. **Environment Variables Set** (.env file)
   ```
   ANTHROPIC_API_KEY=sk-ant-xxx
   ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
   MONGO_URI=mongodb://localhost:27017/
   DB_NAME=MySchool
   ```

5. **Chapter Data in MongoDB**
   - At least one chapter must be scanned via "Setup E-Books"
   - Verify data in `MySchool.scanned_chapters` collection

---

## Test Case 1: Basic Question Generation

### Steps
1. **Login** to the app with any username/password
2. **Navigate** to Academics → Generate Questions
3. **Select** any Class, Subject, and Chapter (must be pre-scanned)
4. **Configure** question types:
   - First row: MCQ, Count: 2, Marks: 1
   - Click "Add" to add a row
   - Second row: Short, Count: 2, Marks: 2
   - Click "Add" to add a row
   - Third row: Long, Count: 1, Marks: 5
5. **Click** "GENERATE QUESTIONS" button
6. **Verify**
   - Loading spinner appears
   - Button text changes to "Generating..."
   - After 10-30 seconds, success message appears
   - Message shows total number of questions generated

### Expected Result
✅ Success message: "✓ Generated 5 questions successfully!"

### Verification
```bash
# In MongoDB
db.questions.find().pretty()

# Should see document with:
# - class, subject, chapter fields
# - questions array with 5 items
# - configuration array with 3 rows
# - generated_by username
# - generated_at timestamp
```

---

## Test Case 2: Validation - Missing Selection

### Steps
1. Navigate to Generate Questions
2. Click "GENERATE QUESTIONS" WITHOUT selecting class/subject/chapter
3. Click again with only class selected
4. Click again with class and subject selected

### Expected Result
❌ Error message: "Select class, subject, and chapter."

---

## Test Case 3: Validation - No Question Rows

### Steps
1. Select Class, Subject, Chapter
2. Delete all question rows (if multiple exist)
3. Click "GENERATE QUESTIONS"

### Expected Result
❌ Error message: "Add at least one question row."

---

## Test Case 4: Validation - Invalid Question Count

### Steps
1. Select Class, Subject, Chapter
2. Enter Question Count: 0 or -5 or "abc"
3. Click "GENERATE QUESTIONS"

### Expected Result
❌ Error message: "Question count must be a positive whole number."

---

## Test Case 5: Validation - Invalid Marks

### Steps
1. Select Class, Subject, Chapter
2. Enter Marks Per Question: 0 or -1 or "xyz"
3. Click "GENERATE QUESTIONS"

### Expected Result
❌ Error message: "Marks per question must be a positive number."

---

## Test Case 6: Validation - Missing Question Type

### Steps
1. Select Class, Subject, Chapter
2. Leave Question Type dropdown empty (or unselected)
3. Enter Count: 2, Marks: 1
4. Click "GENERATE QUESTIONS"

### Expected Result
❌ Error message: "Select a question type for every row."

---

## Test Case 7: Error - Chapter Not Scanned

### Steps
1. Select a Class and Subject that exist
2. Manually create a "fake" chapter name (not scanned)
   - Note: Can't directly do this in UI, so skip this test
   - OR: Delete chapter from `scanned_chapters` and test

### Expected Result
❌ Error message: "Chapter content not found for [ChapterName]. Please scan the e-book first."

---

## Test Case 8: Button State During Generation

### Steps
1. Configure questions as in Test Case 1
2. Click "GENERATE QUESTIONS"
3. While loading:
   - Try clicking button again
   - Try clicking other controls
   - Monitor button state

### Expected Result
- Button is DISABLED during loading
- No double-clicks possible
- Other controls remain enabled
- Progress indicator visible

---

## Test Case 9: Multiple Generations

### Steps
1. Generate questions for Class 10, Physics, Chapter 1
2. Verify success and check MongoDB
3. Generate same questions again
4. Change one parameter (e.g., add a row) and generate
5. Check MongoDB for both generations

### Expected Result
- Each generation creates NEW document in DB
- Different ObjectIds for each
- All documents stored correctly
- Can distinguish by generated_at timestamp

---

## Test Case 10: Question Types Output Validation

### Steps
1. Generate questions with all three types:
   - MCQ (2 questions)
   - Short (2 questions)
   - Long (1 question)
2. Check MongoDB document

### Expected Result
```json
{
  "questions": [
    {
      "type": "mcq",
      "marks": <value>,
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correctOption": "A|B|C|D",
      "answerKey": "..."
    },
    {
      "type": "short",
      "marks": <value>,
      "question": "...",
      "answerKey": "..."  // NO options/correctOption
    },
    {
      "type": "long",
      "marks": <value>,
      "question": "...",
      "answerKey": "..."  // NO options/correctOption
    }
  ]
}
```

✅ MCQ has options array and correctOption
✅ Short/Long have answerKey but NO options
✅ All have proper marks value

---

## Test Case 11: Total Calculation

### Steps
1. Enter Question Count: 3, Marks: 2.5
2. Check Total column
3. Change Count to 5
4. Check Total again
5. Change Marks to 0.5
6. Check Total again

### Expected Results
- First: Total = 3 × 2.5 = 7.5
- Second: Total = 5 × 2.5 = 12.5
- Third: Total = 5 × 0.5 = 2.5

✅ Total updates in real-time as values change

---

## Test Case 12: Add/Delete Buttons

### Steps
1. Start with default 1 row
2. Click "Add" button → Should add row 2
3. Click "Add" button → Should add row 3
4. Try to click "Add" button → Should be DISABLED (max 3 types)
5. Delete row 2 by clicking its "Delete" button
6. Verify only 2 rows remain
7. Delete row 1 → Should be DISABLED (minimum 1 row)
8. Try to delete row 3 → Should be DISABLED (only 1 row left)

### Expected Result
- Add button disables at 3 rows (all question types used)
- Delete button disables with only 1 row
- Dropdown options update (used types show as disabled in other rows)

---

## Test Case 13: Table Layout & Scrolling

### Steps
1. Navigate to Generate Questions
2. Select Class, Subject, Chapter
3. Observe table:
   - Header row with: Question Type, Question Count, Marks Per Question, Total, Add, Delete
   - Data row with aligned columns
   - Fixed column widths
4. On mobile/narrow screen:
   - Try horizontal swipe/drag to scroll
   - Verify no scrollbar visible
   - Content should scroll smoothly

### Expected Result
✅ Clean table layout with aligned columns
✅ Horizontal swipe scrolling works
✅ No visible scrollbar
✅ All columns visible on desktop

---

## Test Case 14: Error Handling - API Down

### Steps
1. Stop the backend API server
2. Try to generate questions
3. Observe error handling

### Expected Result
❌ Error message appears: "Cannot reach the API server..."

---

## Test Case 15: Error Handling - Invalid API Key

### Steps
1. Modify `.env`: `ANTHROPIC_API_KEY=invalid-key-xyz`
2. Restart backend
3. Try to generate questions

### Expected Result
❌ Error message: "Claude denied the API key..."

---

## API Direct Testing (Using curl or Postman)

### Test Endpoint Directly

```bash
curl -X POST http://localhost:8000/api/ebooks/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "Class 10",
    "subject": "Physics",
    "chapter": "Electricity",
    "questionRows": [
      {
        "questionType": "mcq",
        "questionCount": 2,
        "marksPerQuestion": 1
      },
      {
        "questionType": "short",
        "questionCount": 2,
        "marksPerQuestion": 2
      }
    ],
    "username": "testuser@example.com"
  }'
```

### Expected Response (Success)
```json
{
  "success": true,
  "id": "507f1f77bcf86cd799439011",
  "questions": [
    {
      "type": "mcq",
      "marks": 1,
      "question": "What is...",
      "options": ["A", "B", "C", "D"],
      "correctOption": "A",
      "answerKey": "..."
    },
    ...
  ],
  "message": "Generated 4 questions successfully."
}
```

### Expected Response (Error - No Chapter)
```json
{
  "success": false,
  "error": "Chapter content not found for FakeChapter. Please scan the e-book first."
}
```

---

## MongoDB Verification

### Check Saved Questions

```bash
# Connect to MongoDB
mongosh

# Use database
use MySchool

# View all generated questions
db.questions.find().pretty()

# View specific chapter's questions
db.questions.findOne({
  "class": "Class 10",
  "subject": "Physics",
  "chapter": "Electricity"
})

# Count questions for a chapter
db.questions.countDocuments({
  "class": "Class 10"
})

# Check configuration of last generation
db.questions.findOne({}, { sort: { generated_at: -1 } })
```

---

## Performance Testing

### Measure Generation Time
1. Click "GENERATE QUESTIONS"
2. Note start time
3. Wait for success message
4. Note end time
5. Calculate duration

### Expected Time Range
- Typical: 10-30 seconds
- Network dependent: 5-60 seconds

### Monitor Resources During Generation
- CPU: May spike while Claude is processing
- Memory: Check for memory leaks
- Network: Should see single HTTP request

---

## Regression Testing

### After Each Change
1. Run all Test Cases 1-13
2. Verify no new errors
3. Check backward compatibility with existing data

### Production Readiness Checklist
- [ ] All error messages display correctly
- [ ] Loading indicator works
- [ ] Button state management correct
- [ ] Database inserts verified
- [ ] MongoDB collection auto-created
- [ ] Timestamps recorded properly
- [ ] Username tracked correctly
- [ ] No console errors
- [ ] No memory leaks
- [ ] Questions are valid JSON
- [ ] API response time acceptable
- [ ] Concurrent generations don't conflict

---

## Debugging Tips

### Check Backend Logs
```bash
# Watch API logs while generating
# Backend should show:
# - POST /api/ebooks/generate-questions
# - Fetching chapter content
# - Calling Claude API
# - Saving to database
# - Returning response
```

### Check Frontend Logs
```bash
# Open browser DevTools → Console
# Should see:
# - No errors
# - API call success
# - Response with questions
```

### Check MongoDB
```bash
# Verify data structure
db.questions.findOne({})

# Check for duplicate questions
db.questions.find().count()

# Verify user tracking
db.questions.distinct("generated_by")

# Check timestamp range
db.questions.aggregate([
  { $group: { _id: null, min: { $min: "$generated_at" }, max: { $max: "$generated_at" } } }
])
```

### Common Issues & Solutions

**Issue:** Loading spinner never stops
- **Solution:** Check backend is running, API key is valid

**Issue:** "Generating..." but no response for 2+ minutes
- **Solution:** Claude API slow or network issue, check backend logs

**Issue:** Questions not in database
- **Solution:** Check MongoDB connection, verify db.questions.find()

**Issue:** Same questions generated each time
- **Solution:** This is expected if chapter content is identical

**Issue:** Wrong number of questions
- **Solution:** Check questionCount values in configuration

---

## Summary

Test coverage:
- ✅ Happy path (Test 1)
- ✅ All error scenarios (Tests 2-7)
- ✅ UI state management (Tests 8, 12)
- ✅ Data integrity (Tests 9, 10, 11)
- ✅ Question type validation (Test 10)
- ✅ API direct testing
- ✅ Database verification
- ✅ Performance monitoring

**Total Test Cases:** 15 + API + DB verification

**Estimated Testing Time:** 30-60 minutes for full coverage
