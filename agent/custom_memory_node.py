from typing import Dict, Any

class CustomMemoryNode:
    """
    A simple in-memory short-term memory node for LangGraph.
    Stores conversation state (messages, context) per session/thread.
    """
    def __init__(self):
        self.memory_store: Dict[str, Any] = {}

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Assume state contains a 'thread_id' and 'messages'
        thread_id = state.get('thread_id', 'default')
        messages = state.get('messages', [])
        # Update memory for this thread
        self.memory_store[thread_id] = messages
        # Add memory to state for agent/tool use
        state['memory'] = self.memory_store[thread_id]
        return state 