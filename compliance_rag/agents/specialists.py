import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from compliance_rag.config import llm_config
from compliance_rag.core.state import ComplianceState, AgentOutput
from compliance_rag.tools.retrieval import policy_search_tool, policy_metadata_tool

# 1. Planner Agent
def planner_node(state: ComplianceState) -> Dict[str, Any]:
    """Decides which agents to call and in what order."""
    sop = state["sop"]
    request = state["initial_request"]
    
    # We use the planner LLM (Llama 3.1) which is configured for JSON output
    planner_llm = llm_config["planner"]
    
    prompt = f"""
    {sop.planner_prompt}
    
    User Request: {request}
    
    Respond in JSON with:
    {{
        "tasks": [
            {{"agent": "researcher", "reasoning": "...", "query": "..."}},
            {{"agent": "sql_analyst", "reasoning": "...", "query": "..."}}
        ]
    }}
    """
    
    response = planner_llm.invoke([HumanMessage(content=prompt)])
    plan = json.loads(response.content)
    
    return {"plan": plan}

# 2. Researcher Agent (Policy Search)
def researcher_node(state: ComplianceState) -> Dict[str, Any]:
    """Retrieves unstructured policy snippets."""
    tasks = state["plan"].get("tasks", [])
    researcher_tasks = [t for t in tasks if t["agent"] == "researcher"]
    
    findings = []
    for task in researcher_tasks:
        result = policy_search_tool.invoke({
            "query": task["query"], 
            "k": state["sop"].researcher_retriever_k
        })
        findings.append(f"Query: {task['query']}\nResults:\n{result}")
    
    output = AgentOutput(agent_name="researcher", findings="\n\n".join(findings))
    return {"agent_outputs": state["agent_outputs"] + [output]}

# 3. SQL Analyst Agent (Metadata Search)
def sql_analyst_node(state: ComplianceState) -> Dict[str, Any]:
    """Generates and executes SQL for metadata."""
    tasks = state["plan"].get("tasks", [])
    sql_tasks = [t for t in tasks if t["agent"] == "sql_analyst"]
    
    if not sql_tasks:
        return {}

    llm = llm_config["sql_analyst"]
    findings = []
    
    for task in sql_tasks:
        # Prompt LLM to generate SQL
        prompt = f"""
        Generate a DuckDB SQL query to answer this task: '{task['query']}'
        Table name: 'policies'
        Columns: policy_id, title, owner, version, last_updated, department, status, retention_years.
        
        ONLY return the SQL query, no explanation.
        """
        sql_query = llm.invoke([HumanMessage(content=prompt)]).content.strip().replace("```sql", "").replace("```", "")
        
        result = policy_metadata_tool.invoke({"sql_query": sql_query})
        findings.append(f"SQL: {sql_query}\nResult:\n{result}")
        
    output = AgentOutput(agent_name="sql_analyst", findings="\n\n".join(findings))
    return {"agent_outputs": state["agent_outputs"] + [output]}

# 4. Synthesizer Agent
def synthesizer_node(state: ComplianceState) -> Dict[str, Any]:
    """Drafts the final response with citations."""
    sop = state["sop"]
    findings = "\n\n".join([f"Agent {o.agent_name} found:\n{o.findings}" for o in state["agent_outputs"]])
    
    llm = llm_config["synthesizer"]
    
    prompt = f"""
    {sop.synthesizer_prompt}
    
    Context from Research:
    {findings}
    
    User Original Request: {state['initial_request']}
    
    Final Answer:
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_response": response.content}
