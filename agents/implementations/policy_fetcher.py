from typing import Dict, Any
import aiohttp
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from ..interfaces import IPolicyFetcher, RefundPolicy
from loguru import logger

class OpenAIPolicyFetcher(IPolicyFetcher):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.policy_urls = {
            "amazon": "https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7",
            "ubereats": "https://help.uber.com/ubereats/article/uber-eats-refund-policy",
            "airbnb": "https://www.airbnb.com/help/article/1320/airbnb-guest-refund-policy",
        }
        
    async def fetch_policy(self, platform: str) -> RefundPolicy:
        """Fetch and analyze refund policy for a given platform"""
        try:
            # Get policy text from platform's website
            policy_text = await self._fetch_policy_text(platform)
            
            # Analyze policy using GPT-4
            analysis = await self._analyze_policy(platform, policy_text)
            
            return RefundPolicy(
                platform=platform,
                policy_text=policy_text,
                eligibility_criteria=analysis["eligibility_criteria"],
                time_limits=analysis["time_limits"],
                required_evidence=analysis["required_evidence"]
            )
            
        except Exception as e:
            logger.error(f"Error fetching policy for {platform}: {str(e)}")
            # Return a basic policy if we can't fetch the actual one
            return self._get_fallback_policy(platform)

    async def _fetch_policy_text(self, platform: str) -> str:
        """Fetch policy text from platform website"""
        if platform not in self.policy_urls:
            return f"No policy URL configured for {platform}"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.policy_urls[platform]) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    return soup.get_text()
        except Exception as e:
            logger.error(f"Error fetching policy text: {str(e)}")
            return f"Error fetching policy for {platform}"

    async def _analyze_policy(self, platform: str, policy_text: str) -> Dict[str, Any]:
        """Analyze policy text using GPT-4"""
        prompt = f"""
        Analyze this {platform} refund policy and extract:
        1. Eligibility criteria for refunds
        2. Time limits for different types of refunds
        3. Required evidence or documentation
        
        Policy Text:
        {policy_text[:2000]}  # Truncate to avoid token limits
        
        Format the response as JSON with these keys:
        - eligibility_criteria: dict of conditions
        - time_limits: dict of timeframes in hours
        - required_evidence: list of required documents/evidence
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            logger.error("Error parsing GPT-4 response as JSON")
            return self._get_fallback_analysis()

    def _get_fallback_policy(self, platform: str) -> RefundPolicy:
        """Return a basic fallback policy when actual policy can't be fetched"""
        return RefundPolicy(
            platform=platform,
            policy_text="Standard refund policy applies",
            eligibility_criteria={
                "damaged": "Item received damaged",
                "not_as_described": "Item not as described",
                "not_received": "Item not received"
            },
            time_limits={
                "standard": 30 * 24,  # 30 days in hours
                "damaged": 48,        # 48 hours
                "not_received": 7 * 24 # 7 days in hours
            },
            required_evidence=[
                "Order number",
                "Photos of damaged items",
                "Description of issue"
            ]
        )

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Return fallback analysis structure"""
        return {
            "eligibility_criteria": {
                "standard": "Standard return window",
                "damaged": "Item received damaged",
                "not_as_described": "Item not as described"
            },
            "time_limits": {
                "standard": 30 * 24,  # 30 days in hours
                "damaged": 48         # 48 hours
            },
            "required_evidence": [
                "Order number",
                "Photos (if applicable)",
                "Description of issue"
            ]
        } 