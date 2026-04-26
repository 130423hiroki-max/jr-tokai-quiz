import streamlit as st
import csv
import random

st.title("🚄 JR東海 歴史テスト")

# --- 1. CSVの読み込み（utf-8-sig に戻しました） ---
@st.cache_data
def load_quiz_data():
    quizzes = []
    try:
        with open('quiz_data.csv', mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                quizzes.append(row)
    except FileNotFoundError:
        return None
    return quizzes

all_quizzes = load_quiz_data()

if all_quizzes is None:
    st.error("⚠️ 同じフォルダに「quiz_data.csv」が見つかりません。")
    st.stop()


# --- 2. 状態（セッション）の初期化 ---
# 出題する50問を固定
if 'selected_quizzes' not in st.session_state:
    question_count = min(50, len(all_quizzes))
    st.session_state.selected_quizzes = random.sample(all_quizzes, question_count)

# 「回答中」か「結果表示中」かを判定するスイッチ
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

quiz_list = st.session_state.selected_quizzes


# ==========================================
# 画面の表示切り替え（回答モード / 結果モード）
# ==========================================

if not st.session_state.show_results:
    # -------------------------
    # 【回答入力モード】の画面
    # -------------------------
    st.info("💡 **【回答時のルール】**\n\n「年」や「駅」は省略して入力してください。\n複数回答問題の順番は問いません。")
    st.write(f"今回は全 {len(all_quizzes)}問 の中から、ランダムで **{len(quiz_list)}問** が出題されています。")

    with st.form("quiz_form"):
        for i, q in enumerate(quiz_list):
            q_num = i + 1
            st.subheader(f"第{q_num}問")
            st.write(q['問題文'])
            
            # 単一回答問題の場合
            if q['タイプ'] == "single":
                st.text_input("答え", key=f"q_{q_num}")
                
            # 複数回答問題の場合
            elif q['タイプ'] == "multiple":
                correct_answers = q['解答'].split(',')
                ans_count = len(correct_answers)
                st.markdown(f"**※{ans_count}つお答えください（順不同）**")
                
                cols = st.columns(min(ans_count, 4))
                for j in range(ans_count):
                    with cols[j % len(cols)]:
                        st.text_input(f"{j+1}つ目", key=f"q_{q_num}_{j}")
                
        # 誤送信防止用のセーフティロック
        st.markdown("---")
        ready_to_submit = st.checkbox("すべての回答を入力し終えました（誤送信防止）")
        
        # 全部の入力が終わったら押すボタン
        submitted = st.form_submit_button("一斉採点する")

        if submitted:
            if not ready_to_submit:
                st.warning("⚠️ 【誤送信防止】\n\nEnterキーなどによる意図しない送信を防ぐため、上の「すべての回答を入力し終えました」にチェックを入れてから、マウスで採点ボタンをクリックしてください。")
            else:
                # ユーザーの回答を安全な場所に保存して、結果モードへ切り替え
                st.session_state.saved_answers = {}
                for i, q in enumerate(quiz_list):
                    q_num = i + 1
                    if q['タイプ'] == 'single':
                        st.session_state.saved_answers[f"q_{q_num}"] = st.session_state.get(f"q_{q_num}", "")
                    elif q['タイプ'] == 'multiple':
                        ans_count = len(q['解答'].split(','))
                        for j in range(ans_count):
                            st.session_state.saved_answers[f"q_{q_num}_{j}"] = st.session_state.get(f"q_{q_num}_{j}", "")
                
                st.session_state.show_results = True
                st.rerun()

else:
    # -------------------------
    # 【採点結果モード】の画面
    # -------------------------
    st.header("💯 採点結果")
    st.write("各問題の採点結果と解説です。復習に役立ててください。")
    st.markdown("---")
    
    score = 0
    
    for i, q in enumerate(quiz_list):
        q_num = i + 1
        st.subheader(f"第{q_num}問")
        st.write(q['問題文'])
        
        # 単一回答問題の採点と表示
        if q['タイプ'] == "single":
            user_ans = st.session_state.saved_answers.get(f"q_{q_num}", "")
            display_ans = user_ans if user_ans != "" else "(未入力)"
            st.write(f"📝 **あなたの回答:** {display_ans}")
            
            correct_ans = q['解答'].strip()
            cleaned_user_ans = user_ans.strip().upper().replace("駅", "")
            
            if cleaned_user_ans == correct_ans.upper():
                st.success(f"**正解！**\n\n💡 **解説:** {q['解説']}")
                score += 1
            else:
                st.error(f"**不正解...** （正解は「{correct_ans}」です）\n\n💡 **解説:** {q['解説']}")
                
        # 複数回答問題の採点と表示
        elif q['タイプ'] == "multiple":
            correct_answers = q['解答'].split(',')
            ans_count = len(correct_answers)
            
            user_ans_list = []
            for j in range(ans_count):
                user_ans_list.append(st.session_state.saved_answers.get(f"q_{q_num}_{j}", ""))
                
            display_user_ans = "、".join([a if a != "" else "(未入力)" for a in user_ans_list])
            st.write(f"📝 **あなたの回答:** {display_user_ans}")
            
            correct_set = set([ans.strip() for ans in correct_answers])
            user_set = set()
            for a in user_ans_list:
                cleaned_a = a.strip().replace("駅", "")
                if cleaned_a != "":
                    user_set.add(cleaned_a)
                    
            if user_set == correct_set:
                st.success(f"**大正解！すべて完璧です！**\n\n💡 **解説:** {q['解説']}")
                score += 1
            else:
                correct_count = len(user_set & correct_set)
                correct_str = "、".join(correct_set)
                st.error(f"**惜しい！** {len(correct_set)}つ中 {correct_count} つ正解です。（正解は「{correct_str}」です）\n\n💡 **解説:** {q['解説']}")
                
        st.markdown("---")
        
    # 最終スコアと再挑戦ボタン
    st.info(f"### あなたの最終スコアは **{len(quiz_list)}問中 {score}問** です！")
    
    if st.button("違う問題で再挑戦する"):
        # 次のテストのために状態をすべてリセットする
        st.session_state.show_results = False
        del st.session_state.selected_quizzes
        del st.session_state.saved_answers
        for key in list(st.session_state.keys()):
            if key.startswith("q_"):
                del st.session_state[key]
        st.rerun()