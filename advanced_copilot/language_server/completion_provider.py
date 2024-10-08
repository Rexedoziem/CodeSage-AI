from typing import List, Tuple, AsyncGenerator
from advanced_copilot.model.architecture.llama2_model import LLaMA2CodeCompletion
from advanced_copilot.model.personalization.adaptive_learning import AdaptiveLearningManager
from advanced_copilot.multi_language.language_detector import LanguageDetector
from advanced_copilot.language_server.performance.caching import Cache
from advanced_copilot.language_server.performance.request_throttler import RequestThrottler
#from .advanced_copilot.model.inference.rag import RAGModel
from advanced_copilot.language_server.suggestion.filter import CompletionFilter
from advanced_copilot.language_server.suggestion.ranker import CompletionRanker
from code_analyzer import CodeAnalyzer
from error_analyzer import ErrorAnalyzer
from error_fixer import ErrorFixer


class CompletionProvider:
    def __init__(self, base_model_path: str, device: str, token: str): #rag_model_path: str, device: str
        self.base_model = LLaMA2CodeCompletion('Rexe/llama-3.1-codegen-merged', device='cpu', token="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")
        #self.rag_model = RAGModel(rag_model_path, device)
        self.adaptive_learning = AdaptiveLearningManager(self.base_model)
        self.language_detector = LanguageDetector()
        self.cache = Cache()
        self.filter = CompletionFilter()
        self.ranker = CompletionRanker()
        self.throttler = RequestThrottler()
        self.code_analyzer = CodeAnalyzer()
        self.error_analyzer = ErrorAnalyzer()
        self.error_fixer = ErrorFixer()

    async def get_inline_completions(self, user_id: str, code_context: str, file_path: str, max_length: int = 20, num_suggestions: int = 3) -> AsyncGenerator[Tuple[str, str, dict], None]:
        language = self.language_detector.detect_language(code_context)
        issues = self.code_analyzer.analyze_code(code_context, file_path)
        
        cache_key = (user_id, code_context, str(issues))
        cached_completions = self.cache.get(cache_key)
        if cached_completions:
            for completion in cached_completions:
                yield completion, language, issues
            return

        personalized_model = await self.adaptive_learning.personalize_model(user_id)
        raw_completions = await personalized_model.generate(code_context, max_length=max_length, num_return_sequences=num_suggestions * 2)
        
        filtered_completions = self.filter.apply(raw_completions, code_context, language)
        ranked_completions = self.ranker.apply(filtered_completions, code_context, language)
        
        completions = ranked_completions[:num_suggestions]
        self.cache.set(cache_key, completions)
        for completion in completions:
            yield completion, language, issues

    async def get_completions_stream(self, user_id: str, code_context: str, max_length: int = 50, num_suggestions: int = 5) -> AsyncGenerator[Tuple[str, str], None]:
        language = self.language_detector.detect_language(code_context)
        personalized_model = await self.adaptive_learning.personalize_model(user_id)
        
        raw_completions = []
        async for completion in personalized_model.generate_stream(code_context, max_length=max_length, num_return_sequences=num_suggestions * 2):
            raw_completions.append(completion)
        
        filtered_completions = self.filter.apply(raw_completions, code_context, language)
        ranked_completions = self.ranker.apply(filtered_completions, code_context, language)
        
        for completion in ranked_completions[:num_suggestions]:
            yield completion, language

    async def get_completions_and_fixes(self, user_id: str, code_context: str, max_length: int = 50, num_suggestions: int = 5) -> AsyncGenerator[Tuple[str, str], None]:
        language = self.language_detector.detect_language(code_context)
        
        if language == 'python':
            errors = self.error_analyzer.analyze_python_code(code_context)
            if errors:
                fixes = self.error_fixer.suggest_fixes(errors, code_context)
                for fix in fixes:
                    yield fix, 'error_fix'
        
        async for completion, _ in self.get_completions_stream(user_id, code_context, max_length, num_suggestions):
            yield completion, 'completion'

    @RequestThrottler.throttle
    async def update_user_model(self, user_id: str, code_snippet: str, accepted: bool):
        adaptive_learning.update_user_model(user_id, code_snippet, accepted)

