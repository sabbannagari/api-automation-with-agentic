import os
import sys
import json
from typing import Dict, Any, List, Optional


class LLMClient:
    """
    Unified LLM client supporting multiple vendors (Anthropic, OpenAI, Google, etc.)

    Handles API key validation, vendor-specific API calls, and response normalization.
    """

    # Load supported vendors from JSON config
    _VENDORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "llm_vendors.json")
    SUPPORTED_VENDORS = {}

    @classmethod
    def _load_vendors_config(cls):
        """Load vendor configurations from JSON file"""
        if not cls.SUPPORTED_VENDORS:
            with open(cls._VENDORS_CONFIG_PATH, 'r') as f:
                cls.SUPPORTED_VENDORS = json.load(f)

    def __init__(self, vendor: str, model: str, temperature: float = 0):
        """
        Initialize LLM client for a specific vendor

        Args:
            vendor: LLM vendor name (anthropic, openai, google, azure, cohere)
            model: Model name/identifier
            temperature: Temperature for response generation (0-1)

        Raises:
            ValueError: If vendor is not supported
            SystemExit: If API key is not set for the vendor
        """
        # Load vendors config if not already loaded
        self._load_vendors_config()

        self.vendor = vendor.lower()
        self.model = model
        self.temperature = temperature

        # Validate vendor
        if self.vendor not in self.SUPPORTED_VENDORS:
            raise ValueError(
                f"Unsupported vendor: {vendor}. "
                f"Supported vendors: {', '.join(self.SUPPORTED_VENDORS.keys())}"
            )

        # Validate API key
        self._validate_api_key()

        # Initialize vendor-specific client
        self._client = None
        self._init_client()

    def _validate_api_key(self):
        """
        Validate that required API key(s) are set for the vendor

        Raises:
            SystemExit: If required API key is not set
        """
        vendor_info = self.SUPPORTED_VENDORS[self.vendor]
        primary_key = vendor_info["env_var"]
        api_key = os.getenv(primary_key)

        if not api_key or api_key.strip() == "":
            print("\n" + "="*80)
            print(f"❌ AUTHENTICATION ERROR - {self.vendor.upper()}")
            print("="*80)
            print(f"🔑 {primary_key} environment variable is not set")
            print("\n📝 Please set it using one of the following methods:")
            print(f"\n   Option 1 - Export in current session:")
            print(f"   export {primary_key}='your-api-key-here'")
            print(f"\n   Option 2 - Add to your shell profile (~/.bashrc, ~/.zshrc):")
            print(f"   echo 'export {primary_key}=\"your-api-key-here\"' >> ~/.bashrc")
            print(f"\n   Option 3 - Create/update .env file in the project root:")
            print(f"   echo '{primary_key}=your-api-key-here' >> .env")
            print(f"\n🔗 Get your API key from: {vendor_info['console_url']}")
            print("="*80 + "\n")
            sys.exit(1)

        # Check additional env vars for vendors like Azure
        if "additional_env_vars" in vendor_info:
            missing_vars = []
            for var in vendor_info["additional_env_vars"]:
                if not os.getenv(var):
                    missing_vars.append(var)

            if missing_vars:
                print("\n" + "="*80)
                print(f"❌ CONFIGURATION ERROR - {self.vendor.upper()}")
                print("="*80)
                print(f"🔑 Missing required environment variables: {', '.join(missing_vars)}")
                print(f"\n📝 For {self.vendor}, you also need to set:")
                for var in missing_vars:
                    print(f"   export {var}='your-value-here'")
                print("="*80 + "\n")
                sys.exit(1)

    def _init_client(self):
        """Initialize vendor-specific API client"""
        if self.vendor == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        elif self.vendor == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        elif self.vendor == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self._client = genai

        elif self.vendor == "azure":
            from openai import AzureOpenAI
            self._client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-02-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )

        elif self.vendor == "cohere":
            import cohere
            self._client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate response from LLM

        Args:
            system_prompt: System instruction/prompt
            user_message: User message/query
            max_tokens: Maximum tokens in response

        Returns:
            str: Generated response text

        Raises:
            Exception: If API call fails
        """
        if self.vendor == "anthropic":
            return self._generate_anthropic(system_prompt, user_message, max_tokens)
        elif self.vendor == "openai":
            return self._generate_openai(system_prompt, user_message, max_tokens)
        elif self.vendor == "google":
            return self._generate_google(system_prompt, user_message, max_tokens)
        elif self.vendor == "azure":
            return self._generate_azure(system_prompt, user_message, max_tokens)
        elif self.vendor == "cohere":
            return self._generate_cohere(system_prompt, user_message, max_tokens)

    def _generate_anthropic(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        """Generate response using Anthropic Claude API"""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=self.temperature
        )
        return response.content[0].text

    def _generate_openai(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        """Generate response using OpenAI API"""
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def _generate_google(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        """Generate response using Google Gemini API"""
        model = self._client.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt
        )

        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": max_tokens,
        }

        response = model.generate_content(
            user_message,
            generation_config=generation_config
        )
        return response.text

    def _generate_azure(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        """Generate response using Azure OpenAI API"""
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        response = self._client.chat.completions.create(
            model=deployment,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def _generate_cohere(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        """Generate response using Cohere API"""
        # Cohere combines system and user message
        combined_message = f"{system_prompt}\n\nUser: {user_message}"

        response = self._client.generate(
            model=self.model,
            prompt=combined_message,
            max_tokens=max_tokens,
            temperature=self.temperature
        )
        return response.generations[0].text

    @classmethod
    def get_supported_vendors(cls) -> List[str]:
        """Get list of supported LLM vendors"""
        cls._load_vendors_config()
        return list(cls.SUPPORTED_VENDORS.keys())

    @classmethod
    def get_vendor_models(cls, vendor: str) -> List[str]:
        """Get list of models for a specific vendor"""
        cls._load_vendors_config()
        vendor = vendor.lower()
        if vendor in cls.SUPPORTED_VENDORS:
            return cls.SUPPORTED_VENDORS[vendor]["models"]
        return []

    @classmethod
    def validate_vendor_config(cls, vendor: str, model: str) -> bool:
        """
        Validate if vendor and model combination is valid

        Args:
            vendor: Vendor name
            model: Model name

        Returns:
            bool: True if valid, False otherwise
        """
        cls._load_vendors_config()
        vendor = vendor.lower()
        if vendor not in cls.SUPPORTED_VENDORS:
            return False

        # Note: We don't strictly validate model names as vendors frequently add new models
        # This just checks if vendor is supported
        return True

    def __repr__(self) -> str:
        return f"LLMClient(vendor='{self.vendor}', model='{self.model}', temperature={self.temperature})"


# Example usage and testing
if __name__ == "__main__":
    print("LLM Client - Multi-Vendor Support")
    print("="*80)
    print("\nSupported Vendors:")
    for vendor in LLMClient.get_supported_vendors():
        models = LLMClient.get_vendor_models(vendor)
        print(f"\n  {vendor.upper()}:")
        print(f"    API Key: {LLMClient.SUPPORTED_VENDORS[vendor]['env_var']}")
        print(f"    Models: {', '.join(models[:3])}...")

    print("\n" + "="*80)
    print("\nTo use this client, set the appropriate API key environment variable")
    print("and initialize with: LLMClient(vendor='anthropic', model='claude-3-5-sonnet-20241022')")
    print("="*80 + "\n")
