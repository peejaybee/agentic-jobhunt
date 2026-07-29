"""ATS Job Matcher & Scoring Agent - Orchestration Package.

Splits the monolithic orchestrator.py into focused submodules:
  sanitizer   - SafeHTMLSanitizer for XSS mitigation
  filters     - Pure functions for employer/keyword/publisher exclusion, title matching, date parsing
  agents      - ADK agent lifecycle (LocalSkillRegistry, runner setup, ATS scoring, salary filter, validation)
  dashboard   - HTML dashboard generation
  pipeline    - Top-level orchestration (ingestion, filtering, agent evaluation, reporting)
"""

import logging
import sys

from dotenv import load_dotenv


class _DynamicLogHandler(logging.Handler):
    """Reads sys.stderr on every write so log capture works with test redirects."""
    def emit(self, record):
        sys.stderr.write(self.format(record) + "\n")


logging.getLogger().setLevel(logging.INFO)
_log_handler = _DynamicLogHandler()
_log_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(_log_handler)

load_dotenv()

import cache as _cache
_cache.init_db()

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .pipeline import extract_resume_text, run_matching_pipeline, run_pipeline
from .filters import (
    check_employer_exclusion,
    filter_excluded_employers,
    is_job_match,
    load_excluded_keywords,
    load_excluded_publishers,
    parse_pub_date,
)
from .agents import (
    evaluate_and_validate_single_job,
    evaluate_single_job_via_skill,
    filter_job_via_skill,
    validate_job_evaluation,
    LocalSkillRegistry,
    skill_registry,
)
from .sanitizer import SafeHTMLSanitizer, sanitize_html
from .dashboard import generate_dashboard
