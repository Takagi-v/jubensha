def get_ai_response(prompt):
    """
    Simulates a call to an AI agent.
    In a real implementation, this would involve a network call to an AI service.
    For now, it just takes manual input from the console.
    """
    print("----------- AI PROMPT -----------")
    print(prompt)
    print("---------------------------------")
    response = input("Enter AI response: ")
    return response

if __name__ == '__main__':
    # Example usage:
    prompt = "你现在是第一阶段——不在场证明的发言了, 请进行你的陈述。"
    ai_response = get_ai_response(prompt)
    print(f"AI Response: {ai_response}") 