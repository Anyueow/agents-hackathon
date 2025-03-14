from agents import Agent, Runner, function_tool, set_default_openai_key
import os
import secrets

# Set the OpenAI API key both as environment variable and using the setter
os.environ["OPENAI_API_KEY"] =  secrets.OPENAI_API_KEY
set_default_openai_key(secrets.OPENAI_API_KEY)

@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is sunny."


def main():
    # Create an agent with the weather tool
    agent = Agent(
        name="Weather Assistant",
        instructions="You are a helpful assistant that can check the weather.",
        tools=[get_weather],
    )

    # Use run_sync for synchronous execution
    result = Runner.run_sync(agent, "What's the weather in Tokyo?")
    print(result.final_output)
    # Expected output: The weather in Tokyo is sunny.


if __name__ == "__main__":
    main()

