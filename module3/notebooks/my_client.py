import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

async def run_agent_simulation():
    # Configure the client to run the python script as a subprocess
    server_params = StdioServerParameters(
        command="python",
        args=["my_server.py"],
        env=None
    )

    print("🔌 Connecting to Order System MCP...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discovery - What can I do?
            tools = await session.list_tools()
            print(f"\n🛠️  Available Tools: {[t.name for t in tools.tools]}")
            
            # 2. Action - Check Order Status
            print("\n🤖 Agent: Checking status for ORD-123...")
            result = await session.call_tool("get_order_status", arguments={"order_id": "ORD-123"})
            print(f"📦 Tool Output: {result.content[0].text}")
            
            # 3. Knowledge - Read Logs
            print("\n🤖 Agent: Reading system logs...")
            logs = await session.read_resource("system://logs")
            print(f"📄 Resource Content: {logs.contents[0].text}")
            
            # 4. Context - Load Prompt
            print("\n🤖 Agent: Loading refund policy for Alice...")
            prompt = await session.get_prompt("refund_policy", arguments={"customer_name": "Alice"})
            
            # Print all messages in the prompt
            print("🧠 Prompt Messages:")
            for i, msg in enumerate(prompt.messages):
                role = msg.role  # "user" or "assistant"
                text = msg.content.text
                print(f"   [{role.upper()}]: {text[:80]}...")

if __name__ == "__main__":
    asyncio.run(run_agent_simulation())
