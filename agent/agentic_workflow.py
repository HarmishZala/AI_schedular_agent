
from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from tools.calendar_tool import CalendarTool

class GraphBuilder():
    def __init__(self,model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()
        self.tools = []
        self.calendar_tools = CalendarTool()
        self.tools.extend(self.calendar_tools.calendar_tool_list)
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.graph = None
        self.system_prompt = SYSTEM_PROMPT

    def agent_function(self, state: MessagesState):
        """Main agent function. Maintains short-term memory of last 8 messages (user and AI)."""
        messages = state["messages"]
        # Keep only the last 8 messages for short-term memory
        if len(messages) > 8:
            messages = messages[-8:]
        input_question = [self.system_prompt] + messages
        response = self.llm_with_tools.invoke(input_question)
        # Update state with new message, again keeping only last 8
        new_messages = messages + [response]
        if len(new_messages) > 8:
            new_messages = new_messages[-8:]
        return {"messages": new_messages}

    def build_graph(self):
        graph_builder = StateGraph(MessagesState)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("agent", END)
        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.build_graph()