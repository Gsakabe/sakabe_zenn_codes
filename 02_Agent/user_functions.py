import json
from typing import Any, Callable, Set
from azure.ai.projects import AIProjectClient

def call_unique_agent(client: AIProjectClient, agent_id: str, query: str) -> str:
    print("call_unique_agent")
    thread = client.agents.create_thread()
    
    client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=query
    )
    
    run = client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent_id)
    
    if run.status == "failed":
        error_info = run.last_error if hasattr(run, "last_error") else "unknown error"
        return json.dumps({"error": f"AgentB failed: {error_info}"})
    
    messages = client.agents.list_messages(thread_id=thread.id)
    client.agents.delete_thread(thread.id)
    
    if not messages.get("data"):
        return json.dumps({"response": "(No messages)"})
    
    data = messages["data"]
    assistant_texts = []
    for m in data:
        if m["role"] == "assistant":
            content_list = m.get("content", [])
            for c in content_list:
                if c.get("type") == "text":
                    assistant_texts.append(c["text"]["value"])
    
    final_text = "\n".join(assistant_texts)
    print("agent b:" + final_text)
    return json.dumps({"response": final_text})


def call_cost_effective_agent(client: AIProjectClient, agent_id: str, query: str) -> str:
    print("call_cost_effective_agent")
    thread = client.agents.create_thread()
    client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=query
    )
    run = client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent_id)
    if run.status == "failed":
        error_info = run.last_error if hasattr(run, "last_error") else "unknown error"
        return json.dumps({"error": f"AgentC failed: {error_info}"})
    
    messages = client.agents.list_messages(thread_id=thread.id)
    client.agents.delete_thread(thread.id)
    
    if not messages.get("data"):
        return json.dumps({"response": "(No messages)"})
    
    data = messages["data"]
    assistant_texts = []
    for m in data:
        if m["role"] == "assistant":
            for c in m.get("content", []):
                if c.get("type") == "text":
                    assistant_texts.append(c["text"]["value"])
    
    final_text = "\n".join(assistant_texts)
    print("agent c:" + final_text)
    return json.dumps({"response": final_text})


# Python で FunctionTool として登録する際に利用する関数セット
def get_user_functions(client: AIProjectClient, unique_agent_id: str, cost_agent_id: str) -> Set[Callable[..., Any]]:
    """
    client や各エージェントIDをクロージャに取り込み、
    call_unique_agent, call_cost_effective_agent を返す関数セットを生成
    ここの内部関数のdocstringがtoolに渡されるので注意
    """
    # 内部関数としてclientやagent_idを束縛し直す

    def _call_unique_agent(query: str) -> str:
        """
        UniqueAgentに問い合わせ、結果をJSON文字列で返す。
        """
        return call_unique_agent(client, unique_agent_id, query)

    def _call_cost_effective_agent(query: str) -> str:
        """
        CostEffectiveAgent(AgentC) に問い合わせ、結果をJSON文字列で返す。
        """
        return call_cost_effective_agent(client, cost_agent_id, query)

    return {
        _call_unique_agent,
        _call_cost_effective_agent
    }
