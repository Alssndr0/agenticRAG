from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from typing_extensions import TypedDict
import os 
from typing import List
import json


class CheckResult(TypedDict):
    check_name: str
    passed: bool
    explanation: str


class AgentState(TypedDict):
    document: str
    comparison_document: str
    pending_checks: List[str]
    current_check: str
    check_results: List[CheckResult]
    question: str
    answer: str


# Define the checks and their corresponding rule files
CHECKS = {
    "swift": "data/swift_message_fields.txt",
    "ucp600": "data/ucp_600.txt", 
    "conflict": "data/conflicting.txt"
}


def retrieve_document(document_path: str) -> str:
    """
    Retrieve a document from a given path.
    
    Args:
        document_path (str): The path to the document.
        
    Returns:
        str: The content of the document.
    """
    try:
        with open(document_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Warning: File {document_path} not found. Using placeholder content.")
        return f"[Placeholder content for {document_path}]"
    except Exception as e:
        print(f"Error reading {document_path}: {e}")
        return f"[Error reading {document_path}]"


# LLM setup (LM Studio)
llm = ChatOpenAI(
    openai_api_base=os.environ.get("LLM_API_BASE", "http://localhost:1234/v1"),
    openai_api_key="not-needed",
    model_name="qwen3-30b-a3b-instruct-2507-mlx",
)


def prepare_document(state: AgentState) -> dict:
    """Initialize the checking process by setting up pending checks."""
    print("Preparing document for compliance checks...")
    return {
        "pending_checks": list(CHECKS.keys()),
        "current_check": "",
        "check_results": []
    }


def agent_planner(state: AgentState) -> dict:
    """Plan the next check to execute or move to review if all checks are complete."""
    if state["pending_checks"]:
        next_check = state["pending_checks"][0]
        print(f"Planning next check: {next_check}")
        return {
            "current_check": next_check
        }
    else:
        print("All checks completed, moving to review...")
        return {}


def agent_executor(state: AgentState) -> dict:
    """Execute a specific compliance check on the document."""
    check = state["current_check"]
    check_file = CHECKS[check]
    
    print(f"Executing check: {check}")
    
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
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
                
            parsed = json.loads(content)
            passed = parsed.get("passed", False)
            explanation = parsed.get("explanation", "No explanation provided.")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for {check}: {e}")
            # Fallback: analyze the response content
            content = result.content.lower()
            passed = "passed" in content or "compliant" in content or "yes" in content
            explanation = f"Could not parse JSON response. Raw response: {result.content[:200]}..."
            
    except Exception as e:
        print(f"Error executing check {check}: {e}")
        passed = False
        explanation = f"Error during check execution: {str(e)}"

    # Update check results
    check_results = list(state.get("check_results", []))
    check_results.append({
        "check_name": check,
        "passed": passed,
        "explanation": explanation,
    })
    
    # Remove completed check from pending
    pending = list(state["pending_checks"])
    if pending and pending[0] == check:
        pending.pop(0)
    
    print(f"Check {check} completed. Passed: {passed}")
    
    return {
        "check_results": check_results,
        "pending_checks": pending
    }


def reviewer(state: AgentState) -> dict:
    """Review all completed checks and generate final summary."""
    print("Reviewing all completed checks...")
    
    check_results = state.get("check_results", [])
    
    if not check_results:
        summary = "No checks were completed."
    else:
        # Create detailed summary
        total_checks = len(check_results)
        passed_checks = sum(1 for r in check_results if r["passed"])
        
        summary_lines = [
            f"DOCUMENT COMPLIANCE REPORT",
            f"========================",
            f"Total checks performed: {total_checks}",
            f"Checks passed: {passed_checks}",
            f"Checks failed: {total_checks - passed_checks}",
            f"Overall status: {'COMPLIANT' if passed_checks == total_checks else 'NON-COMPLIANT'}",
            f"",
            f"DETAILED RESULTS:",
        ]
        
        for i, result in enumerate(check_results, 1):
            status = "✓ PASSED" if result["passed"] else "✗ FAILED"
            summary_lines.extend([
                f"{i}. {result['check_name'].upper()} CHECK: {status}",
                f"   Explanation: {result['explanation']}",
                f""
            ])
        
        summary = "\n".join(summary_lines)
    
    print("\n" + summary)
    return {"answer": summary}


def planner_router(state: AgentState) -> str:
    """Route to next node based on whether there are pending checks."""
    if state["pending_checks"]:
        return "agent_executor"
    else:
        return "reviewer"


# Build the state graph
builder = StateGraph(state_schema=AgentState)

# Add nodes
builder.add_node("prepare_document", prepare_document)
builder.add_node("agent_planner", agent_planner)
builder.add_node("agent_executor", agent_executor)
builder.add_node("reviewer", reviewer)

# Add edges
builder.add_edge(START, "prepare_document")
builder.add_edge("prepare_document", "agent_planner")

# Conditional routing from planner
builder.add_conditional_edges(
    "agent_planner", 
    planner_router, 
    {
        "agent_executor": "agent_executor",
        "reviewer": "reviewer"
    }
)

builder.add_edge("agent_executor", "agent_planner")
builder.add_edge("reviewer", END)

# Compile the graph
graph = builder.compile()


def run_compliance_check(document_path: str, question: str = "Please check my document for compliance."):
    """
    Run the complete compliance checking workflow.
    
    Args:
        document_path (str): Path to the document to check
        question (str): Optional question/context for the check
        
    Returns:
        dict: Final state with compliance results
    """
    print(f"Starting compliance check for document: {document_path}")
    
    # Initialize state
    init_state = {
        "document": retrieve_document(document_path),
        "comparison_document": "",
        "pending_checks": [],
        "current_check": "",
        "check_results": [],
        "question": question,
        "answer": ""
    }
    
    # Run the workflow
    result = graph.invoke(init_state)
    return result


if __name__ == "__main__":
    # Example usage
    try:
        result = run_compliance_check("data/bill_of_lading.txt")
        print("\n" + "="*50)
        print("FINAL RESULT:")
        print("="*50)
        print(result["answer"])
    except Exception as e:
        print(f"Error running compliance check: {e}")
        print("Make sure your document files exist in the 'data' directory.")