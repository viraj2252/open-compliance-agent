import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from compliance_rag.config import llm_config
from compliance_rag.core.state import ComplianceState, AgentOutput
from compliance_rag.tools.retrieval import policy_search_tool, policy_metadata_tool
from compliance_rag.utils.json_parser import parse_llm_json

logger = logging.getLogger("compliance_rag.specialists")


# 1. Planner Agent
def planner_node(state: ComplianceState) -> Dict[str, Any]:
    """Decides which agents to call and in what order."""
    sop = state["sop"]
    request = state["initial_request"]
    
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
    
    try:
        response = planner_llm.invoke([HumanMessage(content=prompt)])
        plan = parse_llm_json(response.content)
        
        if not plan or "tasks" not in plan:
            logger.warning("Planner returned invalid plan. Using fallback.")
            plan = {"tasks": [
                {"agent": "researcher", "reasoning": "Fallback search", "query": request}
            ]}
        
        # Validate that each task has a string query
        for task in plan.get("tasks", []):
            if not isinstance(task.get("query"), str):
                task["query"] = str(task.get("query", request))
        
        logger.info(f"Plan created with {len(plan.get('tasks', []))} tasks.")
        return {"plan": plan}
        
    except Exception as e:
        logger.error(f"Planner failed: {e}. Using fallback plan.")
        return {"plan": {"tasks": [
            {"agent": "researcher", "reasoning": "Fallback due to planner error", "query": request}
        ]}}


# 2. Researcher Agent (Policy Search)
def researcher_node(state: ComplianceState) -> Dict[str, Any]:
    """Retrieves unstructured policy snippets."""
    tasks = state["plan"].get("tasks", [])
    researcher_tasks = [t for t in tasks if t["agent"] == "researcher"]
    
    findings = []
    for task in researcher_tasks:
        try:
            query = str(task["query"])  # Ensure string
            result = policy_search_tool.invoke({
                "query": query, 
                "k": state["sop"].researcher_retriever_k
            })
            findings.append(f"Query: {query}\nResults:\n{result}")
            logger.info(f"Researcher found results for: {query[:50]}...")
        except Exception as e:
            logger.error(f"Researcher failed for query '{task.get('query', 'unknown')}': {e}")
            findings.append(f"Query: {task.get('query', 'unknown')}\nResults: Error - {str(e)}")
    
    output = AgentOutput(agent_name="researcher", findings="\n\n".join(findings))
    return {"agent_outputs": state["agent_outputs"] + [output]}


# 3. SQL Analyst Agent (Metadata Search)
def sql_analyst_node(state: ComplianceState) -> Dict[str, Any]:
    """Generates and executes SQL for metadata."""
    tasks = state["plan"].get("tasks", [])
    sql_tasks = [t for t in tasks if t["agent"] == "sql_analyst"]
    
    if not sql_tasks:
        logger.info("No SQL tasks assigned. Skipping.")
        return {}

    llm = llm_config["sql_analyst"]
    findings = []
    
    for task in sql_tasks:
        try:
            prompt = f"""
            Generate a DuckDB SQL query to answer this task: '{task['query']}'
            Table name: 'policies'
            Columns: policy_id, title, owner, version, last_updated, department, status, retention_years.
            
            ONLY return the SQL query, no explanation.
            """
            sql_query = llm.invoke([HumanMessage(content=prompt)]).content.strip()
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            result = policy_metadata_tool.invoke({"sql_query": sql_query})
            findings.append(f"SQL: {sql_query}\nResult:\n{result}")
            logger.info(f"SQL Analyst executed: {sql_query[:80]}...")
        except Exception as e:
            logger.error(f"SQL Analyst failed: {e}")
            findings.append(f"SQL Error: {str(e)}")
        
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
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        logger.info("Synthesizer produced final response.")
        return {"final_response": response.content}
    except Exception as e:
        logger.error(f"Synthesizer failed: {e}")
        return {"final_response": f"Error generating response: {str(e)}"}
