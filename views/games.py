import datetime
import time
import random
import streamlit as st
from models.word import get_translation, get_display
from services.gamification import add_xp


def _build_pool(words: list, custom_words: list, pool_key: str) -> list:
    all_w = words + custom_words
    if pool_key == "haftalik":
        cutoff = str(datetime.date.today() - datetime.timedelta(days=7))
        return [w for w in all_w if st.session_state.progress.get(w["word"], {}).get("last_seen", "") >= cutoff]
    if pool_key == "zor":
        return [w for w in all_w if st.session_state.progress.get(w["word"], {}).get("status") == "hard"]
    return all_w  # genel


def render(words: list, custom_words: list) -> None:
    st.markdown("# 🎮 Kelime Oyunları Merkezi")

    col_sel, col_info = st.columns([2, 3])
    with col_sel:
        pool_opts = {"genel": "🌐 Tüm Kelimeler", "haftalik": "📅 Bu Hafta Çalışılanlar", "zor": "💪 Zor Kelimeler"}
        sel = st.selectbox(
            "Kelime havuzu",
            list(pool_opts.keys()),
            format_func=lambda k: pool_opts[k],
            index=list(pool_opts.keys()).index(st.session_state.get("games_pool", "genel")),
            label_visibility="collapsed",
        )
        if sel != st.session_state.get("games_pool"):
            st.session_state["games_pool"] = sel
            for k in ["match_game", "crossword_game", "anagram_game", "ai_prefix_game", "rapid_quiz", "speed_game", "tf_game"]:
                st.session_state.pop(k, None)
            st.rerun()

    pool = _build_pool(words, custom_words, st.session_state.get("games_pool", "genel"))
    with col_info:
        st.caption(f"Havuzda **{len(pool)}** kelime")
        if len(pool) < 6:
            st.warning("⚠️ Bu havuzda yeterli kelime yok. Farklı bir havuz seç.")

    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🃏 Eşleştirme", "✏️ Kelime Bulmaca", "🔀 Anagram",
        "📝 Präfix Fiil Oyunu", "🎯 Çoktan Seçmeli",
        "⏱️ Süre Yarışı", "✅ Doğru/Yanlış",
    ])
    with tab1: _render_match(pool, words, custom_words)
    with tab2: _render_crossword(pool, words, custom_words)
    with tab3: _render_anagram(pool, words, custom_words)
    with tab4: _render_prefix(words, custom_words)
    with tab5: _render_rapid_quiz(pool, words, custom_words)
    with tab6: _render_speed(pool, words, custom_words)
    with tab7: _render_true_false(pool, words, custom_words)


# ── 1. EŞLEŞTİRME ────────────────────────────────────────────────────────────
def _render_match(pool, words, custom_words):
    st.markdown("### 🃏 Kelime Eşleştirme")
    st.markdown("Almanca kelimeleri doğru Türkçe anlamlarıyla eşleştir!")

    if "match_game" not in st.session_state:
        st.session_state.match_game = {"active": False, "words": [], "selected_german": None,
                                        "score": 0, "attempts": 0, "game_completed": False, "balloon_shown": False}

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Yeni Oyun", key="new_match_game", use_container_width=True):
            avail = [w for w in pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok","—",None,"")]
            if len(avail) >= 4:
                selected = random.sample(avail, min(6, len(avail)))
                game_words = [{"german": w["word"], "article": w.get("article",""),
                               "turkish": get_translation(w["word"], words, custom_words),
                               "matched": False, "id": random.randint(1000,9999)} for w in selected]
                random.shuffle(game_words)
                st.session_state.match_game = {"active": True, "words": game_words, "selected_german": None,
                                               "score": 0, "attempts": 0, "game_completed": False, "balloon_shown": False}
                st.rerun()

    game = st.session_state.match_game
    if not game.get("active"):
        st.info("🎯 Yeni oyun başlatmak için 'Yeni Oyun' butonuna tıkla!")
        return

    words_g = game["words"]
    matched_count = sum(1 for w in words_g if w["matched"])
    total = len(words_g)

    if matched_count == total > 0 and not game.get("balloon_shown"):
        st.balloons(); game["balloon_shown"] = True; game["game_completed"] = True
        st.session_state.match_game = game; st.rerun()

    if game.get("game_completed"):
        st.success(f"🎉 Tebrikler! {game['attempts']} denemede tamamladın! Skor: {game['score']}")
        add_xp(game["score"])
        st.markdown(f"✨ +{game['score']} XP kazandın!")
        if st.button("🔄 Tekrar Oyna", key="match_again"):
            st.session_state.match_game["active"] = False; st.rerun()
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Skor", game["score"]); col2.metric("✅ Eşleşen", f"{matched_count}/{total}"); col3.metric("🔄 Deneme", game["attempts"])
    st.progress(matched_count / total)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 🇩🇪 Almanca")
        for wd in [w for w in words_g if not w["matched"]]:
            disp = f"{wd['article']} {wd['german']}".strip() if wd["article"] else wd["german"]
            is_sel = game["selected_german"] == wd["german"]
            if st.button(disp, key=f"match_{wd['german']}_{wd['id']}", use_container_width=True, type="primary" if is_sel else "secondary"):
                game["selected_german"] = None if is_sel else wd["german"]; st.rerun()
    with col_r:
        st.markdown("### 🇹🇷 Türkçe")
        for tr in list(set([w["turkish"] for w in words_g if not w["matched"]])):
            if st.button(tr, key=f"match_tr_{tr}", use_container_width=True):
                if game["selected_german"] is None:
                    st.warning("⚠️ Önce bir Almanca kelime seçin!")
                else:
                    game["attempts"] += 1
                    sel = next((w for w in words_g if w["german"] == game["selected_german"]), None)
                    if sel and sel["turkish"] == tr:
                        sel["matched"] = True; game["score"] += 10; game["selected_german"] = None; st.success("✅ Doğru!")
                    else:
                        st.error("❌ Yanlış!"); game["selected_german"] = None
                    st.rerun()


# ── 2. BULMACA ────────────────────────────────────────────────────────────────
def _render_crossword(pool, words, custom_words):
    st.markdown("### ✏️ Kelime Bulmaca")
    st.markdown("Verilen ipuçlarına göre doğru kelimeleri bul!")

    if "crossword_game" not in st.session_state:
        st.session_state.crossword_game = {"active": False, "balloon_shown": False}

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Yeni Bulmaca", key="new_crossword", use_container_width=True):
            avail = [w for w in pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok","—")]
            if len(avail) >= 6:
                sel = random.sample(avail, 6)
                cw = [{"word": w["word"], "clue": get_translation(w["word"], words, custom_words),
                        "article": w.get("article",""), "solved": False, "user_answer": ""} for w in sel]
                st.session_state.crossword_game = {"active": True, "words": cw, "score": 0, "attempts": 0, "balloon_shown": False}
                st.rerun()

    game = st.session_state.crossword_game
    if not game.get("active"):
        st.info("📝 Yeni bulmaca başlatmak için 'Yeni Bulmaca' butonuna tıkla!"); return

    ws = game["words"]
    solved = sum(1 for w in ws if w["solved"])
    total = len(ws)

    if solved == total > 0 and not game.get("balloon_shown"):
        st.balloons(); game["balloon_shown"] = True; st.session_state.crossword_game = game; st.rerun()

    if solved == total:
        st.success(f"🎉 Bulmacayı tamamladın! Skor: {game['score']}"); add_xp(game["score"])
        if st.button("🔄 Yeni Bulmaca", key="crossword_again"):
            st.session_state.crossword_game = {"active": False}; st.rerun()
        return

    st.markdown(f"### Çözdüğün Kelimeler: {solved}/{total}")
    st.progress(solved / total)
    for idx, wd in enumerate(ws):
        if not wd["solved"]:
            st.markdown(f"**{idx+1}. İpucu:** {wd['clue']}")
            c1, c2 = st.columns([3, 1])
            with c1:
                ans = st.text_input("Kelime", key=f"cross_{idx}", placeholder=f"{len(wd['word'])} harfli kelime...")
            with c2:
                if st.button("Kontrol Et", key=f"check_{idx}"):
                    game["attempts"] += 1
                    if ans.lower().strip() == wd["word"].lower():
                        wd["solved"] = True; game["score"] += 20; st.success("✅ Doğru! +20 XP"); st.rerun()
                    else:
                        st.error(f"❌ Yanlış! İpucu: {len(wd['word'])} harfli")
            st.markdown("---")


# ── 3. ANAGRAM ────────────────────────────────────────────────────────────────
def _render_anagram(pool, words, custom_words):
    st.markdown("### 🔀 Anagram Oyunu")
    st.markdown("Karışık harfleri doğru sıraya koy!")

    if "anagram_game" not in st.session_state:
        st.session_state.anagram_game = {"active": False, "balloon_shown": False}

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Yeni Anagram", key="new_anagram", use_container_width=True):
            avail = [w for w in pool if 4 <= len(w["word"]) <= 8]
            if avail:
                sel = random.sample(avail, min(10, len(avail)))
                remaining = [{"word": w["word"], "clue": get_translation(w["word"], words, custom_words), "article": w.get("article","")} for w in sel]
                random.shuffle(remaining)
                st.session_state.anagram_game = {"active": True, "current_word": None, "original_word": None,
                                                  "clue": None, "score": 0, "attempts": 0,
                                                  "remaining": remaining, "completed": [], "balloon_shown": False}
                st.rerun()

    game = st.session_state.anagram_game
    if not game.get("active"):
        st.info("🔀 Yeni anagram oyunu başlatmak için 'Yeni Anagram' butonuna tıkla!"); return

    if not game["remaining"] and not game.get("current_word") and not game.get("balloon_shown"):
        st.balloons(); game["balloon_shown"] = True; st.session_state.anagram_game = game; st.rerun()

    if not game["remaining"] and not game.get("current_word"):
        st.success(f"🎉 Anagram oyununu tamamladın! Skor: {game['score']}"); add_xp(game["score"])
        if st.button("🔄 Yeni Oyun", key="anagram_again"):
            st.session_state.anagram_game = {"active": False}; st.rerun()
        return

    if not game.get("current_word") and game["remaining"]:
        nxt = game["remaining"].pop(0)
        game["current_word"] = nxt["word"]; game["original_word"] = nxt["word"]; game["clue"] = nxt["clue"]
        chars = list(nxt["word"]); random.shuffle(chars); game["scrambled"] = " ".join(chars).upper()
        st.session_state.anagram_game = game; st.rerun()

    if game.get("current_word"):
        st.markdown(f"### 📝 İpucu: {game['clue']}")
        st.markdown(f"### 🔀 Karışık Harfler: **{game['scrambled']}**")
        st.markdown(f"💡 Kelime uzunluğu: {len(game['current_word'])} harf")
        c1, c2 = st.columns([3, 1])
        with c1:
            ans = st.text_input("Cevabın:", key="anagram_answer", placeholder="Kelimeyi yaz...")
        with c2:
            if st.button("Kontrol Et", key="check_anagram"):
                game["attempts"] += 1
                if ans.lower().strip() == game["current_word"].lower():
                    game["score"] += 15; st.success("✅ Doğru! +15 XP")
                    game["current_word"] = None; game["scrambled"] = None; game["clue"] = None
                    st.session_state.anagram_game = game; st.rerun()
                else:
                    st.error("❌ Yanlış! Tekrar dene."); st.info(f"💡 İpucu: {game['clue']}")
        st.markdown(f"**Skor:** {game['score']} | **Deneme:** {game['attempts']}")
        if st.button("💡 İpucu Al (-5 XP)", use_container_width=True):
            if game["score"] >= 5:
                game["score"] -= 5; st.info(f"Kelimenin ilk harfi: **{game['current_word'][0].upper()}**")
                st.session_state.anagram_game = game; st.rerun()
            else:
                st.warning("Yeterli puanın yok!")


# ── 4. PRÄFIX FİİL ───────────────────────────────────────────────────────────
def _render_prefix(words, custom_words):
    st.markdown("### 🤖 AI Destekli Präfix Fiil Oyunu")
    st.markdown("Kelime listenizdeki fiillerle önekleri öğrenin!")

    if "ai_prefix_game" not in st.session_state:
        st.session_state.ai_prefix_game = {"active": False, "balloon_shown": False}

    verb_words = [w for w in words + custom_words if w.get("type") == "Verb"]
    verb_groups = _group_verbs(verb_words, words, custom_words)

    if not verb_groups:
        st.warning("⚠️ Yeterli fiil grubu bulunamadı!"); return

    st.success(f"📚 {len(verb_groups)} farklı fiil grubu bulundu!")
    game_mode = st.radio("Oyun Modu:", ["🎯 Hangi Önek?", "✏️ Eşleştirme", "🎲 Rastgele Quiz"], horizontal=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 Oyunu Başlat", key="start_ai_prefix_game", use_container_width=True, type="primary"):
            questions = _build_prefix_questions(verb_groups, game_mode)
            st.session_state.ai_prefix_game = {"active": True, "balloon_shown": False, "mode": game_mode,
                                                "questions": questions[:15], "score": 0, "current_idx": 0,
                                                "matches": [], "selected_left": None}
            st.rerun()

    game = st.session_state.ai_prefix_game
    if not game.get("active"): return

    questions = game["questions"]
    idx = game["current_idx"]

    if idx >= len(questions) and not game.get("balloon_shown"):
        st.balloons(); game["balloon_shown"] = True; st.session_state.ai_prefix_game = game; st.rerun()

    if idx >= len(questions):
        st.markdown(f"## 🎉 Oyun Tamamlandı! Skorun: {game['score']} XP")
        add_xp(game["score"])
        wrong = [q for q in questions if q.get("user_answer") and q.get("user_answer") != q.get("correct")]
        if wrong:
            st.markdown("### 📝 Tekrar Etmen Gerekenler:")
            for wa in wrong[:5]: st.markdown(f"- **{wa.get('verb', wa.get('question',''))}** → {wa.get('correct','?')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Yeni Oyun", key="ai_prefix_again"):
                st.session_state.ai_prefix_game = {"active": False}; st.rerun()
        with col2:
            if st.button("🏠 Ana Sayfa", key="ai_prefix_home"):
                from core.session import PAGE_HOME
                st.session_state.page = PAGE_HOME; st.rerun()
        return

    if not questions: return
    current = questions[idx]
    st.progress(idx / len(questions))
    st.markdown(f"### Soru {idx+1}/{len(questions)} | **Skor:** {game['score']} XP")

    if game["mode"] == "🎯 Hangi Önek?":
        prefix = current.get("correct",""); verb = current["verb"]
        st.markdown(f"**Fiil:** {verb[len(prefix):] if prefix else verb}")
        st.markdown(f"**Anlamı:** {current['meaning']}")
        st.markdown("**Hangi önek bu anlamı veriyor?**")
        cols = st.columns(2)
        for i, opt in enumerate(current["options"]):
            with cols[i % 2]:
                if st.button(f"**{opt}**", key=f"pfx_{idx}_{i}", use_container_width=True):
                    if opt == current["correct"]: game["score"] += 10; st.success(f"✅ Doğru!")
                    else: st.error(f"❌ Yanlış! Doğrusu: {current['correct']}")
                    game["current_idx"] += 1; st.session_state.ai_prefix_game = game; st.rerun()

    elif game["mode"] == "✏️ Eşleştirme":
        st.markdown("### Fiilleri Anlamlarıyla Eşleştir")
        col_l, col_r = st.columns(2)
        unmatched = [q for q in questions if not q.get("matched", False)]
        with col_l:
            st.markdown("**🇩🇪 Fiil**")
            for q in unmatched[:6]:
                if st.button(q["verb"], key=f"ai_ml_{q['verb']}_{idx}", use_container_width=True):
                    game["selected_left"] = None if game.get("selected_left") == q["verb"] else q["verb"]; st.rerun()
        with col_r:
            st.markdown("**🇹🇷 Anlam**")
            for q in unmatched[:6]:
                if st.button(q["meaning"], key=f"ai_mr_{q['meaning']}_{idx}", use_container_width=True):
                    if game.get("selected_left"):
                        left = next((qq for qq in questions if qq["verb"] == game["selected_left"]), None)
                        if left and left["meaning"] == q["meaning"]:
                            left["matched"] = True; game["score"] += 10; st.success("✅ Doğru eşleşme!")
                        else: st.error("❌ Yanlış eşleşme!")
                        game["selected_left"] = None; st.session_state.ai_prefix_game = game; st.rerun()
                    else: st.warning("⚠️ Önce bir fiil seçin!")
        matched_count = sum(1 for q in questions if q.get("matched"))
        if len(questions): st.progress(matched_count / len(questions))

    else:  # Rastgele Quiz
        st.markdown(f"### {current['question']}")
        cols = st.columns(2)
        for i, opt in enumerate(current["options"]):
            with cols[i % 2]:
                if st.button(opt, key=f"ai_quiz_{idx}_{i}", use_container_width=True):
                    if opt == current["correct"]: game["score"] += 10; st.success(f"✅ Doğru! {opt}")
                    else: st.error(f"❌ Yanlış! Doğrusu: {current['correct']}")
                    game["current_idx"] += 1; current["user_answer"] = opt
                    st.session_state.ai_prefix_game = game; st.rerun()


def _group_verbs(verb_words, words, custom_words):
    prefixes = ["auf","ab","an","aus","bei","ein","mit","nach","vor","zu","weg","wieder",
                "fest","los","weiter","zurück","her","hin","durch","über","um","unter"]
    groups = {}
    for v in verb_words:
        word = v["word"]
        tr = get_translation(word, words, custom_words)
        root = word; used_prefix = None
        for p in prefixes:
            if word.startswith(p) and len(word) > len(p):
                root = word[len(p):]; used_prefix = p; break
        if root not in groups:
            groups[root] = {"root_meaning": tr, "verbs": []}
        groups[root]["verbs"].append({"full": word, "prefix": used_prefix, "meaning": tr})
    return {k: v for k, v in groups.items() if len(v["verbs"]) >= 2}


def _build_prefix_questions(verb_groups, game_mode):
    questions = []
    sel_groups = random.sample(list(verb_groups.keys()), min(5, len(verb_groups)))
    for group_root in sel_groups:
        group = verb_groups[group_root]
        verbs = group["verbs"]
        if game_mode == "🎯 Hangi Önek?":
            for v in verbs:
                if v["prefix"]:
                    others = [v2["prefix"] for v2 in verbs if v2["prefix"] and v2["prefix"] != v["prefix"]]
                    if len(others) < 3: others.extend(["auf","ab","an","aus"][:3])
                    opts = [v["prefix"]] + random.sample(others, min(3, len(others)))
                    random.shuffle(opts)
                    questions.append({"type":"prefix","verb":v["full"],"root":group_root,
                                      "meaning":v["meaning"],"correct":v["prefix"],"options":opts})
        elif game_mode == "✏️ Eşleştirme":
            for v in verbs:
                questions.append({"type":"match","verb":v["full"],"meaning":v["meaning"],"matched":False})
            random.shuffle(questions)
        else:
            for v in verbs:
                if v["prefix"]:
                    others = [v2["full"] for v2 in verbs if v2["full"] != v["full"]]
                    if len(others) < 3: others.extend([f"ver{group_root}",f"be{group_root}"])
                    opts = [v["full"]] + random.sample(others, min(3, len(others)))
                    random.shuffle(opts)
                    questions.append({"type":"quiz","question":f"'{v['meaning']}' anlamına gelen fiil hangisidir?",
                                      "correct":v["full"],"options":opts,"root":group_root})
    return questions


# ── 5. HIZLI QUIZ ─────────────────────────────────────────────────────────────
def _render_rapid_quiz(pool, words, custom_words):
    st.markdown("### 🎯 Hızlı Çoktan Seçmeli")
    st.markdown("10 soruluk hızlı quiz ile kendini test et!")

    if "rapid_quiz" not in st.session_state:
        st.session_state.rapid_quiz = {"active": False, "balloon_shown": False}

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 Başlat", key="start_rapid", use_container_width=True):
            avail = [w for w in pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok","—")]
            if len(avail) >= 10:
                qs = []
                for w in random.sample(avail, 10):
                    wrong = random.sample([x["word"] for x in avail if x["word"] != w["word"]], 3)
                    opts = [w["word"]] + wrong; random.shuffle(opts)
                    qs.append({"question": get_translation(w["word"], words, custom_words),
                               "options": opts, "correct": w["word"], "answered": False})
                st.session_state.rapid_quiz = {"active": True, "questions": qs, "score": 0, "current_idx": 0, "balloon_shown": False}
                st.rerun()

    quiz = st.session_state.rapid_quiz
    if not quiz.get("active"):
        st.info("🎯 10 soruluk hızlı quiz başlatmak için 'Başlat' butonuna tıkla!"); return

    qs = quiz["questions"]; idx = quiz["current_idx"]
    if idx >= len(qs) and not quiz.get("balloon_shown"):
        st.balloons(); quiz["balloon_shown"] = True; st.session_state.rapid_quiz = quiz; st.rerun()

    if idx >= len(qs):
        st.success(f"🎉 Quiz tamamlandı! Skor: {quiz['score']}/{len(qs)*10}"); add_xp(quiz["score"])
        if st.button("🔄 Yeni Quiz", key="rapid_again"):
            st.session_state.rapid_quiz = {"active": False}; st.rerun()
        return

    cur = qs[idx]
    st.progress(idx / len(qs))
    st.markdown(f"### Soru {idx+1}/{len(qs)}")
    st.markdown("**Bu kelimenin Almancası nedir?**")
    st.markdown(f"### {cur['question']}")
    for i, opt in enumerate(cur["options"]):
        if st.button(opt, key=f"rapid_{idx}_{i}", use_container_width=True):
            if opt == cur["correct"]: quiz["score"] += 10; st.success("✅ Doğru! +10 XP")
            else: st.error(f"❌ Yanlış! Doğru cevap: {cur['correct']}")
            quiz["current_idx"] += 1; st.session_state.rapid_quiz = quiz; st.rerun()
    st.markdown(f"**Skor:** {quiz['score']} / {len(qs)*10}")


# ── 6. SÜRE YARIŞI ────────────────────────────────────────────────────────────
_SPEED_DURATION = 45  # seconds


def _render_speed(pool, words, custom_words):
    st.markdown("### ⏱️ Süre Yarışı")
    st.markdown("45 saniyede mümkün olduğunca çok doğru cevap ver!")

    if "speed_game" not in st.session_state:
        st.session_state.speed_game = {"active": False}

    game = st.session_state.speed_game

    if not game.get("active"):
        if st.button("🚀 Başlat", key="start_speed", type="primary", use_container_width=True):
            avail = [w for w in pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok", "—")]
            if len(avail) < 4:
                st.warning("Yeterli kelime yok!"); return
            random.shuffle(avail)
            st.session_state.speed_game = {
                "active": True,
                "pool": avail,
                "idx": 0,
                "score": 0,
                "wrong": 0,
                "start_time": time.time(),
                "current": None,
                "feedback": None,
            }
            st.rerun()
        return

    elapsed = time.time() - game["start_time"]
    remaining = max(0, _SPEED_DURATION - elapsed)

    # Süre doldu
    if remaining == 0:
        total = game["score"] + game["wrong"]
        pct = int(game["score"] / total * 100) if total else 0
        if not game.get("balloon_shown"):
            st.balloons()
            game["balloon_shown"] = True
            st.session_state.speed_game = game
        st.markdown(f"## ⏱️ Süre Doldu!")
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Doğru", game["score"])
        c2.metric("❌ Yanlış", game["wrong"])
        c3.metric("🎯 Başarı", f"%{pct}")
        bonus = game["score"] * 5
        add_xp(bonus)
        st.success(f"⚡ +{bonus} XP kazandın!")
        if st.button("🔄 Tekrar Oyna", key="speed_again"):
            st.session_state.speed_game = {"active": False}; st.rerun()
        return

    # Süre çubuğu
    st.markdown(f"### ⏱️ {int(remaining)} saniye")
    st.progress(remaining / _SPEED_DURATION)
    c1, c2 = st.columns(2)
    c1.metric("✅ Doğru", game["score"])
    c2.metric("❌ Yanlış", game["wrong"])

    # Mevcut soruyu hazırla
    if game["current"] is None:
        pool_list = game["pool"]
        widx = game["idx"] % len(pool_list)
        w = pool_list[widx]
        others = [x for x in pool_list if x["word"] != w["word"]]
        wrongs = random.sample(others, min(3, len(others)))
        opts = [get_translation(w["word"], words, custom_words)]
        for wo in wrongs:
            tr = get_translation(wo["word"], words, custom_words)
            if tr not in ("Çeviri yok", "—"):
                opts.append(tr)
        while len(opts) < 4 and len(pool_list) > len(opts):
            extra = get_translation(random.choice(pool_list)["word"], words, custom_words)
            if extra not in opts and extra not in ("Çeviri yok", "—"):
                opts.append(extra)
        random.shuffle(opts)
        game["current"] = {"word": w, "correct_tr": get_translation(w["word"], words, custom_words), "options": opts}
        st.session_state.speed_game = game

    cur = game["current"]
    word = cur["word"]
    art = word.get("article", "")
    display = f"{art} **{word['word']}**".strip() if art else f"**{word['word']}**"
    st.markdown(f"## {display}  `{word.get('type','')}`")

    if game.get("feedback"):
        if game["feedback"] == "correct":
            st.success("✅ Doğru!")
        else:
            st.error(f"❌ Yanlış! → {cur['correct_tr']}")
        game["feedback"] = None
        game["current"] = None
        game["idx"] += 1
        st.session_state.speed_game = game

    cols = st.columns(2)
    for i, opt in enumerate(cur["options"]):
        with cols[i % 2]:
            if st.button(opt, key=f"speed_{game['idx']}_{i}", use_container_width=True):
                if opt == cur["correct_tr"]:
                    game["score"] += 1
                    game["feedback"] = "correct"
                else:
                    game["wrong"] += 1
                    game["feedback"] = "wrong"
                st.session_state.speed_game = game
                st.rerun()

    # Süreyi canlı tut — saniyede bir otomatik yenile
    time.sleep(1)
    st.rerun()


# ── 7. DOĞRU / YANLIŞ ─────────────────────────────────────────────────────────
def _render_true_false(pool, words, custom_words):
    st.markdown("### ✅ Doğru / Yanlış")
    st.markdown("Gösterilen kelime–anlam çifti doğru mu? Hızlıca karar ver!")

    if "tf_game" not in st.session_state:
        st.session_state.tf_game = {"active": False}

    game = st.session_state.tf_game

    if not game.get("active"):
        n = st.slider("Soru sayısı", 10, 30, 20, key="tf_count")
        if st.button("🚀 Başlat", key="start_tf", type="primary", use_container_width=True):
            avail = [w for w in pool if get_translation(w["word"], words, custom_words) not in ("Çeviri yok", "—")]
            if len(avail) < 4:
                st.warning("Yeterli kelime yok!"); return
            pairs = []
            for _ in range(n):
                w = random.choice(avail)
                correct_tr = get_translation(w["word"], words, custom_words)
                is_correct = random.random() > 0.45  # ~55% doğru, biraz bias
                if is_correct:
                    shown_tr = correct_tr
                else:
                    decoy = random.choice([x for x in avail if x["word"] != w["word"]])
                    shown_tr = get_translation(decoy["word"], words, custom_words)
                    if shown_tr in ("Çeviri yok", "—"):
                        shown_tr = correct_tr; is_correct = True
                pairs.append({"word": w, "shown_tr": shown_tr, "is_correct": is_correct, "answered": None})
            st.session_state.tf_game = {
                "active": True, "pairs": pairs, "idx": 0,
                "score": 0, "wrong": 0, "streak": 0, "best_streak": 0,
            }
            st.rerun()
        return

    pairs = game["pairs"]
    idx = game["idx"]

    if idx >= len(pairs):
        total = game["score"] + game["wrong"]
        pct = int(game["score"] / total * 100) if total else 0
        emoji = "🏆" if pct >= 80 else "💪" if pct >= 60 else "📚"
        if not game.get("balloon_shown"):
            st.balloons()
            game["balloon_shown"] = True
            st.session_state.tf_game = game
        st.markdown(f"## {emoji} Oyun Bitti!")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Doğru", game["score"])
        c2.metric("❌ Yanlış", game["wrong"])
        c3.metric("🎯 Başarı", f"%{pct}")
        c4.metric("🔥 En İyi Seri", game["best_streak"])
        bonus = game["score"] * 8
        add_xp(bonus)
        st.success(f"⚡ +{bonus} XP kazandın!")
        if st.button("🔄 Tekrar Oyna", key="tf_again"):
            st.session_state.tf_game = {"active": False}; st.rerun()
        return

    cur = pairs[idx]
    word = cur["word"]
    art = word.get("article", "")
    display = f"{art} {word['word']}".strip() if art else word["word"]

    st.progress(idx / len(pairs))
    st.caption(f"Soru {idx+1}/{len(pairs)}  |  ✅ {game['score']}  ❌ {game['wrong']}  🔥 Seri: {game['streak']}")

    st.markdown(
        f"<div style='text-align:center;padding:2rem 1rem;background:rgba(74,144,217,0.1);"
        f"border-radius:16px;margin:1rem 0;'>"
        f"<div style='font-size:2rem;font-weight:700'>{display}</div>"
        f"<div style='font-size:1.4rem;margin-top:0.5rem;opacity:0.85'>{cur['shown_tr']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if cur["answered"] is None:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Doğru", key=f"tf_yes_{idx}", use_container_width=True, type="primary"):
                _tf_answer(game, idx, True); st.rerun()
        with col2:
            if st.button("❌ Yanlış", key=f"tf_no_{idx}", use_container_width=True):
                _tf_answer(game, idx, False); st.rerun()
    else:
        if cur["answered"]:
            st.success("✅ Doğru bildin!" if cur["is_correct"] else f"❌ Yanlış! Bu çift yanlıştı. Doğru: {get_translation(cur['word']['word'], words, custom_words)}")
        else:
            st.error("❌ Yanlış bildin!" if cur["is_correct"] else "✅ Doğru bildin — bu çift gerçekten yanlıştı!")
        if st.button("Sonraki ➡️", key=f"tf_next_{idx}", type="primary"):
            game["idx"] += 1
            st.session_state.tf_game = game
            st.rerun()


def _tf_answer(game: dict, idx: int, user_says_correct: bool) -> None:
    cur = game["pairs"][idx]
    actually_correct = cur["is_correct"]
    user_right = (user_says_correct == actually_correct)
    cur["answered"] = user_says_correct
    if user_right:
        game["score"] += 1
        game["streak"] += 1
        game["best_streak"] = max(game["best_streak"], game["streak"])
    else:
        game["wrong"] += 1
        game["streak"] = 0
    st.session_state.tf_game = game
