# Premium Dashboard Template for Job Matcher Results

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Job Match Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030712;
            --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
            --glass-bg: rgba(17, 24, 39, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-hover-border: rgba(59, 130, 246, 0.4);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.15);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
            padding: 2rem 1rem;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        /* Header section */
        header {
            text-align: center;
            margin-bottom: 3rem;
            position: relative;
        }

        .logo-glow {
            width: 100px;
            height: 100px;
            background: var(--accent-gradient);
            filter: blur(40px);
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: -1;
            opacity: 0.6;
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 400;
        }

        /* Summary Dashboard card */
        .summary-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            backdrop-filter: blur(12px);
            margin-bottom: 2.5rem;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        }

        .summary-info {
            flex: 1;
            min-width: 250px;
        }

        .summary-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
            font-weight: 600;
        }

        .summary-value {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .summary-value span {
            color: #3b82f6;
        }

        .stats-group {
            display: flex;
            gap: 2rem;
        }

        .stat-item {
            text-align: center;
        }

        .stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }

        .stat-val {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .stat-val.score-high { color: var(--success); }
        .stat-val.score-med { color: var(--warning); }
        .stat-val.score-low { color: var(--danger); }

        /* Job matches list */
        .jobs-list {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .job-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        .job-card:hover {
            transform: translateY(-2px);
            border-color: var(--glass-hover-border);
            box-shadow: 0 12px 30px rgba(59, 130, 246, 0.15);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .job-identity {
            flex: 1;
            min-width: 250px;
        }

        .job-title {
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.35rem;
            letter-spacing: -0.01em;
        }

        .company-name {
            font-size: 1.05rem;
            color: #8b5cf6;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .meta-badges {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
            flex-wrap: wrap;
        }

        .badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .badge.source {
            background: rgba(139, 92, 246, 0.1);
            color: #c084fc;
            border-color: rgba(139, 92, 246, 0.2);
        }

        .badge.category {
            background: rgba(6, 182, 212, 0.1);
            color: #22d3ee;
            border-color: rgba(6, 182, 212, 0.2);
        }

        /* Score circular-like indicator card */
        .score-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
            min-width: 100px;
            text-align: center;
        }

        .score-box.high {
            background: var(--success-glow);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--success);
        }

        .score-box.med {
            background: var(--warning-glow);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: var(--warning);
        }

        .score-box.low {
            background: var(--danger-glow);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: var(--danger);
        }

        .score-num {
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.1;
        }

        .score-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.15rem;
            opacity: 0.8;
        }

        /* Match feedback/explanation */
        .explanation-section {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1.25rem;
            border-left: 3px solid;
        }

        .explanation-section.high { border-left-color: var(--success); }
        .explanation-section.med { border-left-color: var(--warning); }
        .explanation-section.low { border-left-color: var(--danger); }

        .explanation-title {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }

        .explanation-text {
            font-size: 0.925rem;
            color: var(--text-primary);
        }

        /* Collapsible Job Description */
        .collapsible-container {
            margin-bottom: 1rem;
        }

        .collapse-trigger {
            background: none;
            border: none;
            color: #3b82f6;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0;
            transition: color 0.2s;
        }

        .collapse-trigger:hover {
            color: #60a5fa;
            text-decoration: underline;
        }

        .collapse-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }

        .collapse-content.expanded {
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .job-description-content {
            padding: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
            max-height: 350px;
            overflow-y: auto;
            white-space: pre-line;
        }

        .job-description-content::-webkit-scrollbar {
            width: 6px;
        }

        .job-description-content::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }

        .job-description-content::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }

        .job-description-content::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        /* Card footer action buttons */
        .card-actions {
            display: flex;
            justify-content: flex-end;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 1rem;
        }

        .apply-btn {
            background: var(--accent-gradient);
            color: white;
            text-decoration: none;
            padding: 0.6rem 1.25rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            transition: opacity 0.2s, transform 0.2s;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .apply-btn:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }

        .apply-btn:active {
            transform: scale(0.98);
        }

        /* No matches placeholder */
        .no-matches {
            text-align: center;
            padding: 4rem 2rem;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            margin-top: 2rem;
        }

        .no-matches-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        .no-matches-title {
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }

        .no-matches-desc {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        /* Chevron Icon */
        .chevron {
            display: inline-block;
            transition: transform 0.3s;
            font-size: 0.6rem;
        }

        .collapse-trigger.active .chevron {
            transform: rotate(90deg);
        }

        @media (max-width: 600px) {
            .summary-card {
                flex-direction: column;
                align-items: flex-start;
            }
            .stats-group {
                width: 100%;
                justify-content: space-between;
            }
            .card-header {
                flex-direction: column;
            }
            .score-box {
                width: 100%;
                margin-top: 0.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-glow"></div>
            <h1>ATS Job Match Dashboard</h1>
            <div class="subtitle">AI-Powered Remote Job Search & Resume Matching</div>
        </header>

        <!-- Summary Statistics Card -->
        <div class="summary-card">
            <div class="summary-info">
                <div class="summary-title">Resume Evaluated</div>
                <div class="summary-value">{resume_filename}</div>
                <div class="summary-title" style="margin-top: 0.75rem;">Keywords Searched</div>
                <div class="summary-value" style="font-size: 0.95rem; font-weight: 400; color: var(--text-secondary);">
                    {searched_keywords}
                </div>
            </div>
            <div class="stats-group">
                <div class="stat-item">
                    <div class="stat-label">Total Jobs Found</div>
                    <div class="stat-val" style="color: #3b82f6;">{total_found}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Evaluated</div>
                    <div class="stat-val" style="color: #8b5cf6;">{total_evaluated}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Avg Match Score</div>
                    <div class="stat-val {avg_score_class}">{avg_score}%</div>
                </div>
            </div>
        </div>

        <!-- Matches List -->
        <div class="jobs-list">
            {jobs_html_content}
        </div>
    </div>

    <script>
        function toggleDescription(btn, id) {
            const content = document.getElementById(id);
            const isExpanded = content.style.maxHeight && content.style.maxHeight !== '0px';
            
            if (isExpanded) {
                content.style.maxHeight = '0px';
                btn.classList.remove('active');
                setTimeout(() => {
                    content.classList.remove('expanded');
                }, 400);
            } else {
                content.classList.add('expanded');
                // Calculate height of child to animate smoothly
                const inner = content.querySelector('.job-description-content');
                content.style.maxHeight = (inner.scrollHeight + 32) + 'px';
                btn.classList.add('active');
            }
        }
    </script>
</body>
</html>
"""

JOB_CARD_TEMPLATE = """
            <!-- Job Card {index} -->
            <div class="job-card">
                <div class="card-header">
                    <div class="job-identity">
                        <div class="job-title">{job_title}</div>
                        <div class="company-name">
                            {company_name}
                        </div>
                        <div class="meta-badges">
                            <span class="badge source">{source}</span>
                            <span class="badge category">{category}</span>
                            {pub_date_badge}
                        </div>
                    </div>
                    <div class="score-box {score_class}">
                        <div class="score-num">{score}%</div>
                        <div class="score-label">ATS Match</div>
                    </div>
                </div>

                <!-- Explanation / Recruiter Notes -->
                <div class="explanation-section {score_class}">
                    <div class="explanation-title">AI Recruiter Notes</div>
                    <div class="explanation-text">
                        {explanation}
                    </div>
                </div>

                <!-- Collapsible Description -->
                <div class="collapsible-container">
                    <button class="collapse-trigger" onclick="toggleDescription(this, 'desc-{index}')">
                        <span class="chevron">▶</span> View Full Job Description
                    </button>
                    <div id="desc-{index}" class="collapse-content">
                        <div class="job-description-content">
                            {job_description}
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="card-actions">
                    <a href="{job_url}" target="_blank" class="apply-btn">
                        View Posting
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </a>
                </div>
            </div>
"""

NO_MATCHES_TEMPLATE = """
        <div class="no-matches">
            <div class="no-matches-icon">🔍</div>
            <div class="no-matches-title">No Matching Jobs Found</div>
            <div class="no-matches-desc">We couldn't find any remote jobs matching your search criteria. Try broadening your job titles.</div>
        </div>
"""
