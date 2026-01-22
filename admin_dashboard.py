import streamlit as st
import pandas as pd
import uuid
from database import DatabaseService
from utils import *

class AdminDashboard:
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def show(self):
        st.set_page_config(
            page_title="InternTrack | Admin Hub",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.title("Admin Command Hub")
            st.markdown("### Institutional Performance Monitoring & Track Management")
        with col_h2:
            if st.button("Exit Admin Hub", type="secondary", use_container_width=True):
                del st.session_state.role
                st.rerun()
        
        st.markdown("---")
        
        tab_tracks, tab_cohort, tab_analytics = st.tabs(["Track Repository", "Cohort Management", "Advanced Analytics"])
        
        with tab_tracks:
            self.manage_tracks()
        
        with tab_cohort:
            self.manage_cohort()
        
        with tab_analytics:
            self.show_advanced_analytics()
    
    def manage_tracks(self):
        st.header("Learning Track Repository")
        st.markdown("Create, edit, and manage learning tracks for your interns.")
        
        col_add1, col_add2 = st.columns([1, 5])
        with col_add1:
            if st.button("Deploy New Track", type="primary", use_container_width=True):
                st.session_state.show_job_modal = True
                st.session_state.editing_job = None
        
        jobs = self.db.get_jobs()
        
        if not jobs:
            st.info("No learning tracks available. Create your first track to get started!")
        else:
            cols = st.columns(3)
            for idx, job in enumerate(jobs):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                            <div style="
                                border: 1px solid #e2e8f0;
                                border-radius: 1rem;
                                padding: 1.5rem;
                                margin-bottom: 1rem;
                                background: white;
                                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                            ">
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"<span style='background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; color: #64748b;'>{job['domain']}</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"### {job['title']}")
                        
                        st.markdown(f"{job['description'][:80]}..." if len(job['description']) > 80 else job['description'])
                        
                        st.markdown("**Required Skills:**")
                        skills_text = " ".join([f"`{skill['name']} L{skill['minLevel']}`" for skill in job['required_skills'][:3]])
                        st.markdown(skills_text)
                        if len(job['required_skills']) > 3:
                            st.caption(f"+{len(job['required_skills']) - 3} more skills")
                        
                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if st.button("Edit", key=f"edit_{job['id']}", use_container_width=True):
                                st.session_state.show_job_modal = True
                                st.session_state.editing_job = job
                                st.rerun()
                        with col_act2:
                            if st.button("Delete", key=f"del_{job['id']}", type="secondary", use_container_width=True):
                                st.session_state.delete_job_id = job['id']
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        if 'delete_job_id' in st.session_state and st.session_state.delete_job_id:
            st.warning("Are you sure you want to delete this learning track? This action cannot be undone.")
            col_conf1, col_conf2, col_conf3 = st.columns([1, 1, 4])
            with col_conf1:
                if st.button("Yes, Delete", type="primary", use_container_width=True):
                    self.db.delete_job(st.session_state.delete_job_id)
                    del st.session_state.delete_job_id
                    st.success("Track deleted successfully!")
                    time.sleep(1)
                    st.rerun()
            with col_conf2:
                if st.button("Cancel", use_container_width=True):
                    del st.session_state.delete_job_id
                    st.rerun()
        
        if st.session_state.get('show_job_modal', False):
            self.show_job_modal()
    
    def show_job_modal(self):
        editing = st.session_state.get('editing_job')
        
        if editing:
            st.markdown("### Edit Learning Track")
        else:
            st.markdown("### Deploy New Learning Track")
        
        with st.form("job_form", clear_on_submit=False):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                title = st.text_input(
                    "Track Name",
                    value=editing['title'] if editing else "",
                    placeholder="e.g., Frontend Developer"
                )
            with col_info2:
                domain_options = ["Web Development", "Mobile Development", "Machine Learning", "Cloud & DevOps", "Data Science", "Cybersecurity", "UX/UI Design"]
                domain = st.selectbox(
                    "Domain",
                    domain_options,
                    index=domain_options.index(editing['domain']) if editing and editing['domain'] in domain_options else 0
                )
            
            st.markdown("#### Skill Benchmarks")
            skills_input = st.text_area(
                "Required Skills (format: Skill:Level)",
                placeholder="React:4, TypeScript:3, JavaScript:4, CSS:3, HTML:3\nPython:5, MachineLearning:4, TensorFlow:3, Statistics:4",
                value=", ".join([f"{s['name']}:{s['minLevel']}" for s in editing['required_skills']]) if editing else "",
                height=100,
                help="Enter skills with minimum proficiency levels (1-5). One per line or comma separated."
            )
            
            description = st.text_area(
                "Track Description",
                value=editing['description'] if editing else "",
                placeholder="Describe the learning objectives, responsibilities, and outcomes for this track...",
                height=150
            )
            
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                submit_label = "Update Track" if editing else "Deploy Track"
                if st.form_submit_button(submit_label, type="primary", use_container_width=True):
                    if not title:
                        st.error("Track name is required")
                    else:
                        required_skills = []
                        if skills_input:
                            items = skills_input.replace('\n', ',').split(',')
                            for item in items:
                                item = item.strip()
                                if item:
                                    if ':' in item:
                                        parts = item.split(':')
                                        name = parts[0].strip()
                                        level = parts[1].strip() if len(parts) > 1 else '3'
                                        try:
                                            required_skills.append({
                                                "name": name,
                                                "minLevel": int(level)
                                            })
                                        except ValueError:
                                            required_skills.append({
                                                "name": name,
                                                "minLevel": 3
                                            })
                                    else:
                                        required_skills.append({
                                            "name": item,
                                            "minLevel": 3
                                        })
                        
                        job = {
                            "id": editing['id'] if editing else f"job-{uuid.uuid4().hex[:8]}",
                            "title": title,
                            "domain": domain,
                            "description": description,
                            "required_skills": required_skills
                        }
                        
                        self.db.upsert_job(job)
                        st.session_state.show_job_modal = False
                        if 'editing_job' in st.session_state:
                            del st.session_state.editing_job
                        st.success("Track saved successfully!")
                        time.sleep(1)
                        st.rerun()
            
            with col_form2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_job_modal = False
                    if 'editing_job' in st.session_state:
                        del st.session_state.editing_job
                    st.rerun()
    
    def manage_cohort(self):
        st.header("Intern Cohort Management")
        st.markdown("Monitor and manage all registered interns.")
        
        interns = self.db.get_all_interns()
        
        if not interns:
            st.info("No interns registered yet. Interns will appear here once they register.")
            return
        
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        with col_stats1:
            st.metric("Total Interns", len(interns))
        with col_stats2:
            onboarded = sum(1 for i in interns if i['onboarded'])
            st.metric("Onboarded", onboarded)
        with col_stats3:
            active = sum(1 for i in interns if self.db.get_attendance_for_intern(i['id']))
            st.metric("Active", active)
        with col_stats4:
            avg_score = 0
            count = 0
            for intern in interns:
                attendance = self.db.get_attendance_for_intern(intern['id'])
                if attendance:
                    avg_score += sum(a['score'] for a in attendance if a['score']) / len(attendance)
                    count += 1
            st.metric("Avg Score", f"{avg_score/count:.1f}" if count > 0 else "N/A")
        
        st.markdown("---")
        
        col_select, col_details = st.columns([1, 3])
        
        with col_select:
            st.markdown("### Select Intern")
            
            intern_options = [f"{i['name']} ({i['email']})" for i in interns]
            selected_intern_idx = st.selectbox(
                "Choose intern to view details:",
                range(len(intern_options)),
                format_func=lambda x: intern_options[x],
                label_visibility="collapsed"
            )
            
            selected_intern = interns[selected_intern_idx]
            
            st.markdown("#### Quick Stats")
            attendance = self.db.get_attendance_for_intern(selected_intern['id'])
            
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                st.metric("Sessions", len(attendance))
            with col_q2:
                avg_score = sum(a['score'] for a in attendance) / len(attendance) if attendance else 0
                st.metric("Avg Score", f"{avg_score:.1f}")
            
            if selected_intern.get('analysis'):
                similarity = selected_intern['analysis'].get('similarity', 0)
                st.metric("Skill Match", f"{similarity}%")
        
        with col_details:
            if selected_intern:
                self.show_intern_details(selected_intern)
            else:
                st.info("Select an intern from the list to view detailed performance metrics.")
    
    def show_intern_details(self, intern):
        logs = self.db.get_attendance_for_intern(intern['id'])
        job = self.db.get_job_by_id(intern['assigned_job_id']) if intern['assigned_job_id'] else None
        
        st.header(f"{intern['name']} - Performance Profile")
        st.caption(f"Email: {intern['email']} • Track: {job['title'] if job else 'Not assigned'}")
        
        metrics = intern.get('performance_metrics', {})
        
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        with col_metrics1:
            st.metric("Total Sessions", len(logs))
        with col_metrics2:
            total_mins = sum(l['duration'] for l in logs)
            st.metric("Total Minutes", total_mins)
        with col_metrics3:
            avg_score = sum(l['score'] for l in logs) / len(logs) if logs else 0
            st.metric("Avg Score", f"{avg_score:.1f}")
        with col_metrics4:
            status = "On-Track" if intern['onboarded'] else "Pending Onboarding"
            st.metric("Status", status)
        
        st.markdown("---")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### Performance Trends")
            if logs:
                recent_logs = logs[-10:]
                dates = [log['date'] for log in recent_logs]
                scores = [log['score'] for log in recent_logs]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates, y=scores,
                    mode='lines+markers',
                    name='Scores',
                    line=dict(color='#6366f1', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    height=300,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=30, b=20, l=20, r=20),
                    showlegend=False
                )
                fig.update_xaxes(title_text="Date")
                fig.update_yaxes(title_text="Score", range=[0, 10])
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No performance data available yet.")
        
        with col_chart2:
            st.markdown("#### Study Effort Distribution")
            if logs:
                recent_logs = logs[-10:]
                dates = [log['date'] for log in recent_logs]
                durations = [log['duration'] for log in recent_logs]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=dates, y=durations,
                    name='Duration (min)',
                    marker_color='#10b981',
                    text=durations,
                    textposition='auto'
                ))
                
                fig.update_layout(
                    height=300,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=30, b=20, l=20, r=20),
                    showlegend=False
                )
                fig.update_xaxes(title_text="Date")
                fig.update_yaxes(title_text="Duration (minutes)")
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No study effort data available yet.")
        
        st.markdown("#### Skill Analysis")
        if intern.get('analysis'):
            similarity = intern['analysis'].get('similarity', 0)
            
            col_skill1, col_skill2 = st.columns(2)
            with col_skill1:
                fig = create_skill_gap_pie(similarity)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            with col_skill2:
                st.markdown("#### Performance Distribution")
                fig = create_performance_pie_chart(logs)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Skill analysis not available. Intern needs to complete onboarding.")
        
        st.markdown("#### Recent Learning Sessions")
        if logs:
            for log in logs[:5]:
                with st.container():
                    col_log1, col_log2, col_log3 = st.columns([3, 1, 1])
                    with col_log1:
                        st.markdown(f"**{log['task']}**")
                        st.caption(f"{log['date']} • {log['duration']} minutes")
                    with col_log2:
                        score_color = "#10b981" if log['score'] >= 6 else "#ef4444"
                        st.markdown(f"<h3 style='color: {score_color}; margin: 0;'>{log['score']}/10</h3>", unsafe_allow_html=True)
                    with col_log3:
                        status_color = "#10b981" if log['status'] == 'COMPLETED' else "#ef4444"
                        st.markdown(f"<span style='color: {status_color}; font-weight: bold;'>{log['status']}</span>", unsafe_allow_html=True)
                    
                    if log.get('resources'):
                        with st.expander("View Resources"):
                            for res in log['resources'][:3]:
                                st.caption(f"• {res}")
                    
                    st.divider()
        else:
            st.info("No learning sessions recorded yet.")
    
    def show_advanced_analytics(self):
        st.header("Advanced Analytics Dashboard")
        st.markdown("Comprehensive analytics across all interns and tracks.")
        
        interns = self.db.get_all_interns()
        jobs = self.db.get_jobs()
        all_attendance = self.db.get_all_attendance()
        
        if not interns:
            st.info("No data available. Add interns and tracks to see analytics.")
            return
        
        col_ov1, col_ov2, col_ov3, col_ov4 = st.columns(4)
        with col_ov1:
            st.metric("Total Interns", len(interns))
        with col_ov2:
            st.metric("Total Tracks", len(jobs))
        with col_ov3:
            total_sessions = len(all_attendance)
            st.metric("Total Sessions", total_sessions)
        with col_ov4:
            avg_duration = sum(a['duration'] for a in all_attendance) / len(all_attendance) if all_attendance else 0
            st.metric("Avg Session", f"{avg_duration:.0f} min")
        
        st.markdown("---")
        
        st.markdown("#### Track Popularity & Performance")
        if jobs:
            track_data = []
            for job in jobs:
                interns_in_track = [i for i in interns if i['assigned_job_id'] == job['id']]
                if interns_in_track:
                    avg_similarity = 0
                    count = 0
                    for intern in interns_in_track:
                        if intern.get('analysis') and 'similarity' in intern['analysis']:
                            avg_similarity += intern['analysis']['similarity']
                            count += 1
                    
                    track_data.append({
                        "Track": job['title'],
                        "Interns": len(interns_in_track),
                        "Avg Match": avg_similarity / count if count > 0 else 0
                    })
            
            if track_data:
                import plotly.express as px
                df_tracks = pd.DataFrame(track_data)
                fig = px.bar(df_tracks, x='Track', y=['Interns', 'Avg Match'], 
                            barmode='group', title="Track Distribution & Performance")
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Performance Trends Over Time")
        if all_attendance:
            from collections import defaultdict
            daily_scores = defaultdict(list)
            
            for attendance in all_attendance:
                daily_scores[attendance['date']].append(attendance['score'])
            
            dates = sorted(daily_scores.keys())[-30:]
            avg_scores = [sum(daily_scores[d]) / len(daily_scores[d]) for d in dates]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=avg_scores,
                mode='lines+markers',
                name='Daily Avg Score',
                line=dict(color='#6366f1', width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=30, b=20, l=20, r=20),
                showlegend=False
            )
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Average Score", range=[0, 10])
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Top Performing Interns")
        if interns and all_attendance:
            intern_scores = []
            for intern in interns:
                attendance = self.db.get_attendance_for_intern(intern['id'])
                if attendance:
                    avg_score = sum(a['score'] for a in attendance) / len(attendance)
                    total_duration = sum(a['duration'] for a in attendance)
                    intern_scores.append({
                        "Name": intern['name'],
                        "Track": self.db.get_job_by_id(intern['assigned_job_id'])['title'] if intern['assigned_job_id'] else "N/A",
                        "Avg Score": round(avg_score, 1),
                        "Sessions": len(attendance),
                        "Total Hours": round(total_duration / 60, 1)
                    })
            
            if intern_scores:
                df_leaderboard = pd.DataFrame(intern_scores)
                df_leaderboard = df_leaderboard.sort_values('Avg Score', ascending=False).head(10)
                st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
