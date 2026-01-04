"""
Tool-Using Agent Evaluation:Demonstrates Inspect AI's TOOL system and AGENT patterns.

This evaluation tests:
1)Model's ability to recognize when to use tools
2)Correct tool selection
3)Accurate tool usage
4)Proper interpretation of tool results

Tools Implemented:
1)calculator: Basic arithmetic operations
2)lookup_policy: Company policy database
3)search_database: Employee/product database lookup
4)date_calculator: Date arithmetic

Run: inspect eval tool_agent_eval.py@tool_usage_eval --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0
"""

from dotenv import load_dotenv
load_dotenv()

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.solver import generate, system_message, use_tools
from inspect_ai.tool import tool
from inspect_ai.scorer import model_graded_fact

# TOOL DEFINITIONS
@tool
def calculator():
    """Calculate math expressions like 2+2 or 850*0.15"""

    async def execute(expression: str) -> str:
        """
        Evaluate a math expression.

        Args:
            expression: Math expression like "2 + 2" or "850 * 0.15"

        Returns:
            The result as a string
        """
        try:
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters"

            result = eval(expression)

            if isinstance(result, float):
                if result == int(result):
                    return str(int(result))
                return f"{result:.2f}"
            return str(result)
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error: {str(e)}"

    return execute


@tool
def lookup_policy():
    """Look up company policies for leave, expense, travel, hours, remote, benefits."""

    async def execute(policy_type: str) -> str:
        """
        Look up a company policy.

        Args:
            policy_type: One of: leave, expense, travel, hours, remote, benefits

        Returns:
            The policy details
        """
        policies = {
            "leave": "Leave Policy: Employees receive 12 casual leaves, 10 sick leaves, and 15 earned leaves per year. Unused leaves can be carried forward up to 30 days.",
            "expense": "Expense Policy: Maximum monthly reimbursement is $500. Receipts required for claims over $25. Submit within 30 days of expense.",
            "travel": "Travel Policy: Domestic travel allowance is $200/day. International travel allowance is $400/day. Booking must be done 7 days in advance.",
            "hours": "Working Hours: Standard hours are 9 AM to 6 PM, Monday to Friday. Flexible timing available with manager approval.",
            "remote": "Remote Work Policy: Employees can work from home up to 2 days per week. Full remote requires director approval.",
            "benefits": "Benefits: Health insurance for employee and dependents, 401k matching up to 6%, annual bonus up to 15% of base salary."
        }

        result = policies.get(policy_type.lower().strip())
        if result:
            return result

        # Fuzzy matching for common variations
        for key, value in policies.items():
            if key in policy_type.lower() or policy_type.lower() in key:
                return value

        available = ", ".join(policies.keys())
        return f"Policy not found. Available policies: {available}"

    return execute


@tool
def search_database():
    """Search company database for employee, product, or department info."""

    async def execute(query: str, search_type: str = "employee") -> str:
        """
        Search the database.

        Args:
            query: Name or ID to search
            search_type: One of: employee, product, department

        Returns:
            Search results
        """
        # Mock database
        employees = {
            "john smith": "John Smith - Senior Engineer, ID: E001, Department: Engineering, Salary: $95,000",
            "sarah jones": "Sarah Jones - Product Manager, ID: E002, Department: Product, Salary: $105,000",
            "mike chen": "Mike Chen - Data Scientist, ID: E003, Department: Analytics, Salary: $110,000",
            "e001": "John Smith - Senior Engineer, ID: E001, Department: Engineering, Salary: $95,000",
            "e002": "Sarah Jones - Product Manager, ID: E002, Department: Product, Salary: $105,000",
            "e003": "Mike Chen - Data Scientist, ID: E003, Department: Analytics, Salary: $110,000",
        }

        products = {
            "laptop pro": "Laptop Pro - Price: $1,299, Stock: 150 units, Category: Electronics",
            "wireless mouse": "Wireless Mouse - Price: $49, Stock: 500 units, Category: Accessories",
            "monitor 27": "27-inch Monitor - Price: $399, Stock: 75 units, Category: Electronics",
        }

        departments = {
            "engineering": "Engineering Department - Head: Jane Doe, Employees: 45, Budget: $2.5M",
            "product": "Product Department - Head: Bob Wilson, Employees: 12, Budget: $800K",
            "analytics": "Analytics Department - Head: Lisa Park, Employees: 8, Budget: $600K",
        }

        query_lower = query.lower().strip()

        if search_type.lower() == "employee":
            result = employees.get(query_lower)
            if result:
                return result
            return f"Employee '{query}' not found in database."

        elif search_type.lower() == "product":
            result = products.get(query_lower)
            if result:
                return result
            return f"Product '{query}' not found in database."

        elif search_type.lower() == "department":
            result = departments.get(query_lower)
            if result:
                return result
            return f"Department '{query}' not found in database."

        return f"Invalid search type '{search_type}'. Use: employee, product, or department"

    return execute


@tool
def date_calculator():
    """
    Perform date calculations.

    Use this tool for:
    - Adding/subtracting days from dates
    - Calculating days between dates
    - Finding day of week
    """
    async def execute(operation: str, date1: str, date2_or_days: str = "") -> str:
        """
        Perform date calculations.

        Args:
            operation: The operation to perform.
                      Options: "add_days", "subtract_days", "days_between", "day_of_week"
            date1: First date in YYYY-MM-DD format
            date2_or_days: Second date (for days_between) or number of days (for add/subtract)

        Returns:
            Result of the date calculation.
        """
        from datetime import datetime, timedelta

        try:
            dt1 = datetime.strptime(date1, "%Y-%m-%d")

            if operation == "add_days":
                days = int(date2_or_days)
                result = dt1 + timedelta(days=days)
                return f"Result: {result.strftime('%Y-%m-%d')} ({result.strftime('%A')})"

            elif operation == "subtract_days":
                days = int(date2_or_days)
                result = dt1 - timedelta(days=days)
                return f"Result: {result.strftime('%Y-%m-%d')} ({result.strftime('%A')})"

            elif operation == "days_between":
                dt2 = datetime.strptime(date2_or_days, "%Y-%m-%d")
                diff = abs((dt2 - dt1).days)
                return f"Days between: {diff} days"

            elif operation == "day_of_week":
                return f"Day of week: {dt1.strftime('%A')}"

            else:
                return f"Unknown operation: {operation}. Use: add_days, subtract_days, days_between, day_of_week"

        except ValueError as e:
            return f"Error: Invalid date format. Use YYYY-MM-DD. Details: {str(e)}"

    return execute

# SYSTEM PROMPTS

TOOL_AGENT_PROMPT = """You are a helpful assistant with access to tools.

INSTRUCTIONS:
1. When asked a question, determine if you need to use a tool
2. Use the appropriate tool to get accurate information
3. If calculation is needed, use the calculator tool
4. If policy information is needed, use the lookup_policy tool
5. If employee/product/department info is needed, use search_database
6. If date calculation is needed, use date_calculator
7. Provide a clear, concise answer based on tool results

Always use tools when available rather than guessing or using prior knowledge."""

# TASKS

def load_tool_samples_by_type(tool_type=None):
      """Load tool_agent samples, optionally filtered by requires_tool"""
      import csv
      import json
      samples = []
      with open("../data/all_samples.csv", "r", encoding="utf-8") as f:
          reader = csv.DictReader(f)
          for row in reader:
              if row["eval_type"] == "tool_agent":
                  extra = json.loads(row.get("extra_metadata", "{}"))
                  requires = extra.get("requires_tool", "")
                  if tool_type is None or tool_type in requires:
                      samples.append(Sample(
                          input=row["input"],
                          target=row["target"],
                          metadata={
                              "category": row["category"],
                              "expected_behavior": row["expected_behavior"],
                              "eval_type": row["eval_type"],
                              "requires_tool": requires,
                              "difficulty": extra.get("difficulty", "")
                          }
                      ))
      return MemoryDataset(samples)

@task
def tool_usage_eval():
    """
    Evaluate model's ability to use tools correctly.
    Loads from all_samples.csv with eval_type filter.

    Tests:
    - Tool selection (choosing the right tool)
    - Tool usage (calling with correct arguments)
    - Result interpretation (using tool output correctly)
    """
    return Task(
        dataset=load_tool_samples_by_type(),
        solver=[
            system_message(TOOL_AGENT_PROMPT),
            use_tools([
                calculator(),
                lookup_policy(),
                search_database(),
                date_calculator()
            ]),
            generate()
        ],
        scorer=model_graded_fact()
    )


@task
def calculator_eval():
    """Focused evaluation on calculator tool usage."""

    return Task(
        dataset=load_tool_samples_by_type("calculator"),
        solver=[
            system_message("You have access to a calculator. Use it for all math questions."),
            use_tools([calculator()]),
            generate()
        ],
        scorer=model_graded_fact()
    )


@task
def policy_lookup_eval():
    """Focused evaluation on policy lookup tool."""

    return Task(
        dataset=load_tool_samples_by_type("lookup_policy"),
        solver=[
            system_message("You have access to company policies. Look them up to answer questions."),
            use_tools([lookup_policy()]),
            generate()
        ],
        scorer=model_graded_fact()
    )


@task
def database_search_eval():
    """Focused evaluation on database search tool."""


    return Task(
         dataset=load_tool_samples_by_type("search_database"),
        solver=[
            system_message("You have access to the company database. Search it to answer questions."),
            use_tools([search_database()]),
            generate()
        ],
        scorer=model_graded_fact()
    )


@task
def multi_tool_eval():
    """Evaluate model's ability to use multiple tools together."""


    return Task(
        dataset=load_tool_samples_by_type(","),
        solver=[
            system_message("""You have access to multiple tools.
            You may need to use multiple tools to answer complex questions.
            First gather information, then calculate if needed."""),
            use_tools([
                calculator(),
                lookup_policy(),
                search_database(),
                date_calculator()
            ]),
            generate()
        ],
        scorer=model_graded_fact()
    )

# MAIN
if __name__ == "__main__":
    print("""
Tool-Using Agent Evaluation
Tools Available:
1)calculator: Math operations
2)lookup_policy: Company policies
3)search_database: Employee/product/department lookup
4)date_calculator: Date arithmetic

Tasks:
  tool_usage_eval    - Full evaluation (12 samples)
  calculator_eval    - Calculator only (3 samples)
  policy_lookup_eval - Policy lookup only (3 samples)
  database_search_eval - Database search only (3 samples)
  multi_tool_eval    - Multi-tool reasoning

Run:
  inspect eval tool_agent_eval.py@tool_usage_eval --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0

View:
  inspect view
""")
