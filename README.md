# Refund Automation Agent 🤖

An AI-powered agent that automates the process of obtaining refunds or replacements from e-commerce and service platforms. Built with OpenAI's GPT-4, this agent handles the entire refund workflow from initial request to resolution.

## 🎯 Core Features

- **Smart Request Generation**: Crafts professional, policy-aware refund requests
- **Policy Analysis**: Automatically fetches and analyzes platform refund policies
- **Escalation Management**: Intelligently handles rejections with appropriate escalation strategies
- **Receipt Processing**: Extracts and validates order information from receipts
- **Performance Tracking**: Logs and analyzes success rates and response patterns

## 🏗️ Architecture

Built following SOLID principles, the system is modular and easily extensible:

```
agents-hackathon/
├── agents/
│   ├── interfaces.py         # Core interfaces (SOLID design)
│   ├── refund_agent.py      # Main agent orchestrator
│   └── implementations/     
│       ├── openai_message_gen.py
│       ├── policy_fetcher.py
│       └── response_analyzer.py
├── utils/
│   └── logging.py
└── main.py                  # FastAPI application
```

### Key Components

- **RefundAgent**: Orchestrates the refund process
- **PolicyFetcher**: Retrieves platform-specific refund policies
- **MessageGenerator**: Creates refund requests and escalations using GPT-4
- **ResponseAnalyzer**: Analyzes platform responses
- **EvidenceProcessor**: Handles receipt validation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- FastAPI and dependencies

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Anyueow/agents-hackathon.git
cd agents-hackathon
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
   - Create a `secrets.py` file in the root directory
   - Add your API key:
   ```python
   OPENAI_API_KEY = "your-api-key-here"
   ```

### Running the Service

1. Start the FastAPI server:
```bash
python main.py
```

2. Access the API documentation:
   - Open http://localhost:8000/docs in your browser
   - Interactive API documentation will be available

## 📡 API Endpoints

### POST /process-refund
Initiates a new refund request

```python
{
    "platform": "amazon",
    "order_id": "123-456-789",
    "issue_description": "Item arrived damaged",
    "email": "optional@email.com"
}
```

### POST /handle-response/{order_id}
Processes platform response and determines next steps

```python
{
    "platform": "amazon",
    "response": "Response from the platform"
}
```

## 💡 Usage Example

```python
# Example using curl
curl -X POST "http://localhost:8000/process-refund" \
     -H "Content-Type: multipart/form-data" \
     -F "platform=amazon" \
     -F "order_id=123-456-789" \
     -F "issue_description=Item arrived damaged" \
     -F "receipt=@receipt.pdf"
```

## 🛠️ Development

### Adding New Platforms

1. Create a new platform handler in `agents/implementations/`:
```python
from agents.interfaces import IPolicyFetcher

class AmazonPolicyFetcher(IPolicyFetcher):
    async def fetch_policy(self, platform: str) -> RefundPolicy:
        # Implementation
        pass
```

2. Register the implementation in `main.py`

### Running Tests

```bash
pytest tests/
```

## 📊 Monitoring

The agent logs detailed information about:
- Request success rates
- Response patterns
- Escalation effectiveness
- Processing times

Logs are stored in `data/response_logs/app.log`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

- Follow SOLID principles
- Keep files under 200 lines
- Add tests for new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI framework
- The open-source community 