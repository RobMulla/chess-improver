# Chess Improver - Web UI Implementation Plan

## 🎯 Goal
Complete web UI for fully self-contained solution. All features accessible through browser.

---

## 📊 Current Status Assessment

### ✅ COMPLETED (Backend)
- Game import from Chess.com/Lichess ✅
- Background analysis with Stockfish ✅
- Win% algorithm (Lichess method) ✅
- Move classification (best/good/mistake/blunder) ✅
- Redis caching for performance ✅
- Database models (games + positions) ✅
- 100% accuracy bug FIXED ✅
- Test suite 70/70 passing ✅

### ✅ COMPLETED (Web UI - Basic)
- Dashboard page ✅
- Games list page ✅
- Game viewer (interactive board) ✅
- Practice mode (basic) ✅
- Insights page (skeleton) ✅
- Sidebar navigation ✅

### ❌ MISSING (Critical for Full Web Solution)

#### 1. **Game Import UI** ⚠️ CRITICAL
**Problem:** No way to import games through UI
**Needed:**
- [ ] Settings/Import page
- [ ] Form to enter Chess.com/Lichess username
- [ ] "Sync Games" button
- [ ] Progress indicator during import
- [ ] Status messages (success/error)

**Current:** Must use CLI `python cli/sync_games.py`

---

#### 2. **Bulk Analysis UI** ⚠️ CRITICAL
**Problem:** Can't trigger analysis from UI
**Needed:**
- [ ] "Analyze Selected" button on games list
- [ ] "Analyze All Unanalyzed" button
- [ ] Progress bar showing analysis status
- [ ] Background job status indicator
- [ ] Estimated time remaining

**Current:** Must use CLI or auto-analyzes gradually

---

#### 3. **Download Game Data** ⚠️ IMPORTANT
**Problem:** No export functionality
**Needed:**
- [ ] "Export to PGN" button (single game)
- [ ] "Export All" button (bulk download)
- [ ] Export with/without analysis annotations
- [ ] Download as .zip for bulk

**Current:** Must query database directly

---

#### 4. **Opening Analysis** ❌ NOT IMPLEMENTED
**Problem:** Shows "Unknown" for most games
**Needed:**
- [ ] Opening name detection (ECO codes)
- [ ] Opening performance stats
- [ ] Opening repertoire page
- [ ] Filter games by opening

**Current:** `opening_name` always "Unknown"

---

#### 5. **Insights Dashboard** ⚠️ INCOMPLETE
**Problem:** Shows placeholder data
**Needed:**
- [ ] Accuracy trend chart (Chart.js)
- [ ] Mistake distribution pie chart
- [ ] Opening performance table
- [ ] Game phase breakdown
- [ ] Real data from database

**Current:** Static HTML + "No insights yet"

---

#### 6. **Practice Mode Enhancement** ⚠️ BASIC
**Problem:** Works but limited features
**Needed:**
- [ ] Filter by mistake type
- [ ] Filter by game phase
- [ ] Filter by time period
- [ ] Session stats/scoring
- [ ] Progress tracking
- [ ] Feedback messages

**Current:** Random positions, basic feedback

---

## 🚀 Implementation Roadmap

### **Phase 1: Critical UI Features** (Week 1)
Make system fully self-contained through web UI

**Priority:**
1. **Settings/Import Page**
   - Add `/settings` route
   - Form for username input
   - Trigger sync_games from UI
   - Show progress/status

2. **Bulk Analysis Controls**
   - Add "Analyze" buttons to games list
   - API endpoint `/api/analyze` (POST)
   - Job queue integration
   - Status polling endpoint

3. **Export Functionality**
   - Add "Export PGN" button to game viewer
   - Add "Export All" to games list
   - Generate PGN files on-demand
   - Serve as downloads

### **Phase 2: Data Visualization** (Week 2)
Populate insights with real data

**Priority:**
4. **Opening Detection**
   - Integrate `chess-openings` library
   - Detect opening names from first moves
   - Update database with opening info
   - Filter games by opening

5. **Insights Dashboard**
   - Query real game data
   - Generate Chart.js visualizations
   - Accuracy trends over time
   - Mistake distribution charts
   - Opening performance stats

### **Phase 3: Practice Enhancement** (Week 3)
Make practice mode engaging and effective

**Priority:**
6. **Practice Filters**
   - UI for filter selection
   - Query positions by criteria
   - Session configuration
   - Progress tracking

7. **Gamification**
   - Streak counter
   - Daily goals
   - Achievement system
   - Session stats

---

## 📝 Detailed Task Breakdown

### Task 1.1: Settings/Import Page
```python
# File: src/web/app.py
@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/sync-games', methods=['POST'])
def api_sync_games():
    username = request.json['username']
    platform = request.json['platform']
    # Trigger background job
    job = queue.enqueue(sync_games_task, username, platform)
    return jsonify({'job_id': job.id})

@app.route('/api/job-status/<job_id>')
def job_status(job_id):
    job = Job.fetch(job_id, connection=redis_conn)
    return jsonify({
        'status': job.get_status(),
        'result': job.result
    })
```

```html
<!-- File: src/web/templates/settings.html -->
<form id="sync-form">
  <input type="text" name="username" placeholder="Chess.com username">
  <select name="platform">
    <option value="chesscom">Chess.com</option>
    <option value="lichess">Lichess</option>
  </select>
  <button type="submit">Sync Games</button>
</form>
<div id="progress" style="display:none">
  Syncing... <span id="status"></span>
</div>
```

### Task 1.2: Bulk Analysis
```python
@app.route('/api/analyze-games', methods=['POST'])
def api_analyze_games():
    game_ids = request.json.get('game_ids', [])
    if not game_ids:  # Analyze all
        session = get_session()
        games = session.query(Game).filter_by(analyzed=False).all()
        game_ids = [g.id for g in games]
        session.close()

    # Queue analysis jobs
    jobs = []
    for game_id in game_ids:
        job = queue.enqueue(analyze_game_task, game_id)
        jobs.append(job.id)

    return jsonify({'job_ids': jobs, 'total': len(jobs)})
```

### Task 1.3: Export PGN
```python
@app.route('/api/export-pgn/<game_id>')
def export_pgn(game_id):
    session = get_session()
    game = session.query(Game).filter_by(game_id=game_id).first()

    # Add analysis annotations to PGN
    pgn_with_analysis = add_analysis_to_pgn(game)

    return Response(
        pgn_with_analysis,
        mimetype='application/x-chess-pgn',
        headers={'Content-Disposition': f'attachment; filename=game_{game_id}.pgn'}
    )
```

---

## 🎯 Success Criteria

**Fully Web-Based Solution When:**
- ✅ User can import games without CLI
- ✅ User can analyze games without CLI
- ✅ User can download game data
- ✅ User can see opening names
- ✅ User can view insights with real data
- ✅ User can practice with filters
- ✅ All features work through browser

**Quality Metrics:**
- All pages load < 2s
- No JavaScript errors in console
- Mobile-responsive design
- 90%+ test coverage for new code

---

## 🔄 Next Immediate Steps

1. **Create `/settings` page** with game import form
2. **Add API endpoints** for sync + analysis
3. **Test end-to-end** flow through browser
4. **Document** in README for users

**Estimated Time:** 2-3 days for Phase 1 (critical features)
