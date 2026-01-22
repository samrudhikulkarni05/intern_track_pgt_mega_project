import streamlit as st
import time
from datetime import datetime, date
from database import DatabaseService
from ai_service import AIService
from utils import *

class InternDashboard:
    def __init__(self, db: DatabaseService, ai: AIService):
        self.db = db
        self.ai = ai
    
    def show(self):
        user = st.session_state.current_user
        
        st.set_page_config(
            page_title=f"InternTrack | {user['name']}'s Dashboard",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
        with col_header1:
            st.markdown(f"""
                <h1 style="margin: 0; color: #1e293b;">Welcome back, <span style="color: #6366f1;">{user['name']}</span></h1>
                <p style="margin: 0; color: #64748b; font-size: 0.9rem;">
                    {user['email']} • Learning Dashboard
                </p>
            """, unsafe_allow_html=True)
        with col_header2:
            st.markdown("""
                <div style="text-align: right;">
                    <span style="font-size: 0.8rem; color: #64748b; font-weight: 600; letter-spacing: 0.1em;">
                        INTERN ACCESS
                    </span>
                </div>
            """, unsafe_allow_html=True)
        with col_header3:
            if st.button("Exit Portal", type="secondary", use_container_width=True):
                del st.session_state.role
                del st.session_state.current_user
                st.rerun()
        
        st.markdown("---")
        
        if not user['onboarded']:
            self.onboard_intern(user)
            return
        
        job = self.db.get_job_by_id(user['assigned_job_id'])
        attendance = self.db.get_attendance_for_intern(user['id'])
        
        if attendance and user.get('analysis'):
            performance_metrics = self.ai.get_performance_analysis(attendance, user.get('analysis', {}))
            user['performance_metrics'] = performance_metrics
            self.db.update_intern(user)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            self.show_profile_overview(user, job)
        
        with col2:
            self.show_performance_analytics(user, attendance)
        
        with col3:
            self.show_learning_session(user, attendance)
    
    def show_profile_overview(self, user, job):
        st.markdown("### Track Overview")
        
        with st.container():
            st.markdown(f"**Assigned Role:**")
            st.markdown(f"### {job['title']}")
            st.caption(f"{job['domain']} • {len(job['required_skills'])} required skills")
            
            st.markdown("---")
            
            similarity = user['analysis'].get('similarity', 0) if user['analysis'] else 0
            
            st.markdown("#### Skill Match Score")
            fig = create_skill_gap_pie(similarity)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("---")
            
            st.markdown("#### Your Current Skills")
            if user['skills']:
                for skill in user['skills'][:5]:
                    level = skill.get('level', 0)
                    progress = min(100, (level / 5) * 100)
                    st.markdown(f"**{skill.get('name', 'Skill')}**")
                    st.progress(progress / 100, text=f"Level {level}/5")
            else:
                st.info("No skills assessed yet.")
            
            st.markdown("---")
            
            st.markdown("#### Required Benchmarks")
            for req in job['required_skills'][:3]:
                st.markdown(f"**{req['name']}**")
                st.caption(f"Minimum Level: {req['minLevel']}/5")
    
    def show_performance_analytics(self, user, attendance):
        st.markdown("### Performance Analytics")
        
        fig = create_performance_analysis_chart(attendance, user.get('performance_metrics', {}))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        
        tab_gaps, tab_rec_videos, tab_rec_docs = st.tabs(["Identified Gaps", "Learning Videos", "Documentation"])
        
        with tab_gaps:
            if user['analysis'] and 'gaps' in user['analysis']:
                for gap in user['analysis']['gaps'][:5]:
                    with st.expander(f"**{gap.get('skill', 'Skill')}** | Priority: {gap.get('priority', 'MEDIUM')}", expanded=True):
                        col_g1, col_g2 = st.columns([1, 2])
                        with col_g1:
                            st.metric("Current Level", gap.get('currentLevel', 0))
                            st.metric("Required Level", gap.get('requiredLevel', 0))
                            st.metric("Gap", gap.get('gapLevel', 0))
                        with col_g2:
                            st.markdown("**Analysis:**")
                            st.write(gap.get('reason', 'No detailed analysis available.'))
                            st.caption(f"Estimated improvement time: {gap.get('estimatedImprovementTime', 'Not specified')}")
            else:
                st.info("No skill gaps identified yet.")
        
        with tab_rec_videos:
            if user['analysis'] and 'recommendations' in user['analysis'] and 'videos' in user['analysis']['recommendations']:
                videos = user['analysis']['recommendations']['videos']
                for video in videos[:5]:
                    with st.container():
                        col_v1, col_v2 = st.columns([3, 1])
                        with col_v1:
                            st.markdown(f"#### [{video.get('title', 'Video')}]({video.get('url', '#')})")
                            st.caption(f"{video.get('description', 'No description')}")
                        with col_v2:
                            st.caption(f"{video.get('duration', 'Unknown')}")
                            st.caption(f"{video.get('level', 'All levels')}")
                        st.divider()
            else:
                st.info("No video recommendations available.")
        
        with tab_rec_docs:
            if user['analysis'] and 'recommendations' in user['analysis'] and 'documentation' in user['analysis']['recommendations']:
                docs = user['analysis']['recommendations']['documentation']
                for doc in docs[:5]:
                    with st.container():
                        col_d1, col_d2 = st.columns([3, 1])
                        with col_d1:
                            st.markdown(f"#### [{doc.get('title', 'Documentation')}]({doc.get('url', '#')})")
                            st.caption(f"{doc.get('description', 'No description')}")
                        with col_d2:
                            st.caption(f"{doc.get('type', 'Resource')}")
                        st.divider()
            else:
                st.info("No documentation recommendations available.")
        
        st.markdown("---")
        
        st.markdown("### Recent Activity")
        if attendance:
            for log in attendance[:3]:
                with st.container():
                    col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
                    with col_a1:
                        st.markdown(f"**{log['task']}**")
                        st.caption(f"{log['date']} • {log['duration']} minutes")
                    with col_a2:
                        score_color = "#10b981" if log['score'] >= 6 else "#ef4444"
                        st.markdown(f"<h3 style='color: {score_color}; margin: 0;'>{log['score']}/10</h3>", unsafe_allow_html=True)
                    with col_a3:
                        status_color = "#10b981" if log['status'] == 'COMPLETED' else "#ef4444"
                        st.markdown(f"<span style='color: {status_color}; font-weight: bold;'>{log['status']}</span>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.info("No learning sessions logged yet.")
    
    def show_learning_session(self, user, attendance):
        st.markdown("### Learning Session")
        
        if 'clocked_in' not in st.session_state:
            st.session_state.clocked_in = False
            st.session_state.start_time = None
            st.session_state.resources = []
            st.session_state.task = ""
            st.session_state.show_quiz = False
            st.session_state.quiz_data = []
            st.session_state.quiz_answers = {}
            st.session_state.quiz_feedback = ""
        
        with st.container():
            st.markdown("#### Session Configuration")
            
            task = st.text_area(
                "Learning Objective",
                placeholder="What specific concept or skill are you focusing on today?",
                disabled=st.session_state.clocked_in,
                value=st.session_state.task,
                key="task_input",
                height=100
            )
            
            st.markdown("#### Learning Resources")
            st.caption("Add URLs to resources you'll be studying")
            
            resource_input_container = st.container()
            with resource_input_container:
                resource_col1, resource_col2 = st.columns([4, 1])
                with resource_col1:
                    resource_input = st.text_input(
                        "Resource URL",
                        placeholder="https://...",
                        key="resource_input",
                        label_visibility="collapsed",
                        disabled=st.session_state.clocked_in
                    )
                with resource_col2:
                    if st.button("Add", disabled=st.session_state.clocked_in, use_container_width=True):
                        if resource_input and resource_input not in st.session_state.resources:
                            st.session_state.resources.append(resource_input)
                            st.rerun()
            
            if st.session_state.resources:
                st.markdown("**Added Resources:**")
                for i, res in enumerate(st.session_state.resources):
                    col_r1, col_r2 = st.columns([5, 1])
                    with col_r1:
                        st.caption(f"{i+1}. {res[:50]}...")
                    with col_r2:
                        if not st.session_state.clocked_in:
                            if st.button("Delete", key=f"del_res_{i}"):
                                st.session_state.resources.pop(i)
                                st.rerun()
            
            st.markdown("#### Session Timer")
            
            if st.session_state.clocked_in:
                elapsed = int(time.time() - st.session_state.start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    st.metric("Hours", f"{hours:02d}")
                with col_t2:
                    st.metric("Minutes", f"{minutes:02d}")
                with col_t3:
                    st.metric("Seconds", f"{seconds:02d}")
                
                if st.button("End Session & Take Quiz", type="primary", use_container_width=True):
                    if task and st.session_state.resources:
                        with st.spinner("Generating assessment questions..."):
                            quiz_data = self.ai.get_daily_quiz(task, st.session_state.resources)
                            st.session_state.quiz_data = quiz_data
                            st.session_state.quiz_answers = {}
                            st.session_state.show_quiz = True
                            st.session_state.clocked_in = False
                        st.rerun()
                    else:
                        st.error("Please specify a learning objective and add at least one resource.")
            else:
                if st.button("Start Learning Session", type="primary", use_container_width=True):
                    if task and st.session_state.resources:
                        st.session_state.clocked_in = True
                        st.session_state.start_time = time.time()
                        st.session_state.task = task
                        st.success("Session started! Focus on your learning objective.")
                        st.rerun()
                    else:
                        st.error("Please specify a learning objective and add at least one resource.")
        
        st.markdown("---")
        
        st.markdown("### Score Velocity Analysis")
        if attendance:
            fig = create_score_velocity_chart(attendance)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            if user.get('performance_metrics'):
                metrics = user['performance_metrics']
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Overall Score", f"{metrics.get('overallScore', 0):.1f}/10")
                with col_m2:
                    st.metric("Consistency", f"{metrics.get('consistency', 0):.0f}%")
                with col_m3:
                    improvement = metrics.get('improvementRate', 0)
                    arrow = "↑" if improvement > 0 else "↓" if improvement < 0 else "→"
                    st.metric("Improvement Rate", f"{improvement:+.1f}%", delta=arrow)
        else:
            st.info("Your performance analytics will appear here after your first session.")
        
        if st.session_state.get('show_quiz', False):
            self.show_quiz_modal(user)
    
    def show_quiz_modal(self, user):
        st.markdown("---")
        
        col_qh1, col_qh2 = st.columns([3, 1])
        with col_qh1:
            st.markdown("## Mastery Verification Quiz")
            st.markdown(f"**Learning Context:** {st.session_state.task}")
        with col_qh2:
            if st.button("Cancel Quiz", type="secondary"):
                st.session_state.show_quiz = False
                st.session_state.quiz_data = []
                st.session_state.quiz_answers = {}
                st.rerun()
        
        st.markdown("### Answer all questions to complete your learning session")
        
        quiz_data = st.session_state.quiz_data
        answers = st.session_state.quiz_answers
        
        for i, question in enumerate(quiz_data):
            st.markdown(f"#### Question {i+1}/{len(quiz_data)}")
            st.markdown(f"**{question['question']}**")
            
            options = question['options']
            selected_index = answers.get(i)
            
            selected_option = st.radio(
                f"Select your answer for Question {i+1}:",
                options,
                key=f"quiz_q_{i}",
                index=selected_index if selected_index is not None else None,
                label_visibility="collapsed"
            )
            
            if selected_option:
                st.session_state.quiz_answers[i] = options.index(selected_option)
        
        if st.button("Submit Assessment", type="primary", use_container_width=True):
            score = 0
            correct_answers = []
            incorrect_answers = []
            strengths = []
            weaknesses = []
            
            for i, question in enumerate(quiz_data):
                if i in st.session_state.quiz_answers:
                    if st.session_state.quiz_answers[i] == question['correctAnswer']:
                        score += 1
                        correct_answers.append(i)
                    else:
                        incorrect_answers.append(i)
            
            total_questions = len(quiz_data)
            percentage = (score / total_questions) * 100 if total_questions > 0 else 0
            
            if correct_answers:
                strengths = [f"Q{i+1}" for i in correct_answers[:2]]
            if incorrect_answers:
                weaknesses = [f"Q{i+1}" for i in incorrect_answers[:2]]
            
            duration = int(time.time() - st.session_state.start_time) // 60 if st.session_state.start_time else 0
            feedback = self.ai.get_feedback(
                st.session_state.task,
                score,
                duration,
                {
                    "total_questions": total_questions,
                    "correct_answers": score,
                    "strengths": strengths,
                    "weaknesses": weaknesses
                }
            )
            
            log_entry = {
                "intern_id": user['id'],
                "date": date.today().isoformat(),
                "time_in": datetime.fromtimestamp(st.session_state.start_time).strftime("%H:%M:%S") if st.session_state.start_time else datetime.now().strftime("%H:%M:%S"),
                "time_out": datetime.now().strftime("%H:%M:%S"),
                "task": st.session_state.task,
                "resources": st.session_state.resources,
                "duration": duration,
                "score": score,
                "status": "COMPLETED" if score >= 6 else "NEEDS_REVIEW",
                "quiz_results": {
                    "total_questions": total_questions,
                    "score": score,
                    "percentage": percentage,
                    "correct_answers": correct_answers,
                    "incorrect_answers": incorrect_answers,
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "feedback": feedback
                }
            }
            
            log_id = self.db.log_attendance(log_entry)
            
            if attendance := self.db.get_attendance_for_intern(user['id']):
                performance_metrics = self.ai.get_performance_analysis(attendance, user.get('analysis', {}))
                self.db.update_performance_metrics(user['id'], performance_metrics)
                user['performance_metrics'] = performance_metrics
                self.db.update_intern(user)
            
            st.success("Quiz submitted successfully!")
            
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("Score", f"{score}/{total_questions}")
            with col_r2:
                st.metric("Percentage", f"{percentage:.1f}%")
            with col_r3:
                st.metric("Status", "PASS" if score >= 6 else "REVIEW")
            
            st.markdown("### Detailed Feedback")
            st.info(feedback)
            
            time.sleep(3)
            st.session_state.clocked_in = False
            st.session_state.start_time = None
            st.session_state.resources = []
            st.session_state.task = ""
            st.session_state.show_quiz = False
            st.session_state.quiz_data = []
            st.session_state.quiz_answers = {}
            
            st.rerun()
    
    def onboard_intern(self, user):
        job = self.db.get_job_by_id(user['assigned_job_id'])
        
        st.title("Track Onboarding & Skill Assessment")
        st.markdown("Complete your profile setup to receive personalized learning recommendations.")
        
        col_on1, col_on2 = st.columns([2, 1])
        
        with col_on1:
            with st.container():
                st.markdown(f"### Target Role: {job['title']}")
                st.markdown(f"**Domain:** {job['domain']}")
                st.markdown(job['description'])
                
                st.markdown("#### Required Skills & Levels")
                for skill in job['required_skills']:
                    col_s1, col_s2 = st.columns([3, 1])
                    with col_s1:
                        st.markdown(f"**{skill['name']}**")
                    with col_s2:
                        st.markdown(f"Level {skill['minLevel']}/5 required")
        
        with col_on2:
            with st.container():
                st.markdown("### Skill Self-Assessment")
                st.caption("Rate your proficiency for each required skill (1-5)")
                
                user_skills = []
                for req_skill in job['required_skills']:
                    skill_name = req_skill['name']
                    skill_level = st.slider(
                        f"{skill_name}",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"skill_{skill_name}",
                        help=f"Rate your {skill_name} skill level"
                    )
                    user_skills.append({
                        "name": skill_name,
                        "level": skill_level
                    })
        
        st.markdown("---")
        
        st.markdown("### Quick Assessment Option")
        st.caption("Alternatively, enter your skills in comma-separated format")
        
        quick_input = st.text_area(
            "Enter skills (format: `Skill:Level` or just `Skill` for default level 3)",
            placeholder="React:4, TypeScript:3, JavaScript, CSS:4",
            height=100,
            key="quick_skills_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("Analyze with Quick Input", use_container_width=True):
                if quick_input:
                    parsed_skills = []
                    for item in quick_input.split(','):
                        item = item.strip()
                        if ':' in item:
                            parts = item.split(':')
                            name = parts[0].strip()
                            level = parts[1].strip() if len(parts) > 1 else '3'
                            try:
                                parsed_skills.append({
                                    "name": name,
                                    "level": int(level)
                                })
                            except ValueError:
                                parsed_skills.append({
                                    "name": name,
                                    "level": 3
                                })
                        else:
                            parsed_skills.append({
                                "name": item,
                                "level": 3
                            })
                    user_skills = parsed_skills
        
        with col_btn2:
            if st.button("Complete Onboarding & Generate Analysis", type="primary", use_container_width=True):
                if not user_skills:
                    st.error("Please assess your skills or use the quick input option.")
                else:
                    with st.spinner("Analyzing skill gaps and generating personalized recommendations..."):
                        analysis = self.ai.get_analysis(job, user_skills)
                        
                        user['skills'] = user_skills
                        user['onboarded'] = True
                        user['analysis'] = analysis
                        user['performance_metrics'] = {}
                        self.db.update_intern(user)
                        
                        st.session_state.current_user = user
                        
                        st.success("Onboarding complete! Personalized analysis generated.")
                        time.sleep(2)
                        st.rerun()
