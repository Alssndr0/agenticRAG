import json

from app.configs.ai_config import get_ai_settings
from app.configs.app_config import get_app_settings
from app.schemas.agent_schemas import AgentState
from app.services.tools import retrieve_document
from langchain_openai import ChatOpenAI
from loguru import logger

APP_CONFIG = get_app_settings()
AI_CONFIG = get_ai_settings()

llm = ChatOpenAI(
    openai_api_base=AI_CONFIG.OPENAI_API_BASE,
    api_key=AI_CONFIG.OPENAI_API_KEY,
    model_name=AI_CONFIG.MODEL_NAME,
)

CHECKS = APP_CONFIG.CHECKS


def agent_planner(state: AgentState) -> dict:
    """Plan the next check to execute or move to review if all checks are complete."""
    if state["pending_checks"]:
        next_check = state["pending_checks"][0]
        logger.info(f"Planning next check: {next_check}")
        return {"current_check": next_check}
    else:
        logger.info("All checks completed, moving to review...")
        return {}


def agent_executor(state: AgentState) -> dict:
    """Execute a specific compliance check on the document."""
    check = state["current_check"]
    check_file = CHECKS[check]

    logger.info(f"Executing check: {check}")

    # Retrieve the rules for this check
    check_rules = retrieve_document(check_file)
    doc = state["document"]

    # Create a detailed prompt for the LLM
    prompt = f"""You are a compliance checker. Analyze the following document against the specified rules.

RULES FOR {check.upper()} CHECK:
{check_rules}

DOCUMENT TO CHECK:
{doc}

Please evaluate whether the document complies with the rules and return your response as a JSON object with the following format:
{{"passed": true/false, "explanation": "Detailed explanation of compliance status and any issues found"}}

Be thorough in your analysis and provide specific reasons for your decision."""

    try:
        # Get LLM response
        result = llm.invoke(prompt)

        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            content = result.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            parsed = json.loads(content)
            passed = parsed.get("passed", False)
            explanation = parsed.get("explanation", "No explanation provided.")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for {check}: {e}")
            # Fallback: analyze the response content
            content = result.content.lower()
            passed = "passed" in content or "compliant" in content or "yes" in content
            explanation = f"Could not parse JSON response. Raw response: {result.content[:200]}..."

    except Exception as e:
        logger.error(f"Error executing check {check}: {e}")
        passed = False
        explanation = f"Error during check execution: {str(e)}"

    # Update check results
    check_results = list(state.get("check_results", []))
    check_results.append(
        {
            "check_name": check,
            "passed": passed,
            "explanation": explanation,
        }
    )

    # Remove completed check from pending
    pending = list(state["pending_checks"])
    if pending and pending[0] == check:
        pending.pop(0)

    logger.info(f"Check {check} completed. Passed: {passed}")

    return {"check_results": check_results, "pending_checks": pending}


def reviewer(state: AgentState) -> dict:
    """Review all completed checks and generate final summary."""
    logger.info("Reviewing all completed checks...")

    check_results = state.get("check_results", [])

    if not check_results:
        summary = "No checks were completed."
    else:
        # Create detailed summary
        total_checks = len(check_results)
        passed_checks = sum(1 for r in check_results if r["passed"])

        summary_lines = [
            "DOCUMENT COMPLIANCE REPORT",
            "========================",
            f"Total checks performed: {total_checks}",
            f"Checks passed: {passed_checks}",
            f"Checks failed: {total_checks - passed_checks}",
            f"Overall status: {'COMPLIANT' if passed_checks == total_checks else 'NON-COMPLIANT'}",
            "",
            "DETAILED RESULTS:",
        ]

        for i, result in enumerate(check_results, 1):
            status = "✓ PASSED" if result["passed"] else "✗ FAILED"
            summary_lines.extend(
                [
                    f"{i}. {result['check_name'].upper()} CHECK: {status}",
                    f"   Explanation: {result['explanation']}",
                    "",
                ]
            )

        summary = "\n".join(summary_lines)

    return {"answer": summary}


def planner_router(state: AgentState) -> str:
    """Route to next node based on whether there are pending checks."""
    if state["pending_checks"]:
        return "agent_executor"
    else:
        return "reviewer"
