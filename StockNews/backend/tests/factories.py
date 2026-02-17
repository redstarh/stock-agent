"""factory-boy 테스트 데이터 팩토리.

NewsEvent, ThemeStrength 모델이 구현되면 활성화.
"""

# import factory
# from app.models.news_event import NewsEvent
# from app.models.theme_strength import ThemeStrength


# class NewsEventFactory(factory.Factory):
#     class Meta:
#         model = NewsEvent
#
#     market = "KR"
#     stock_code = "005930"
#     stock_name = "삼성전자"
#     title = factory.Sequence(lambda n: f"테스트 뉴스 {n}")
#     sentiment = "neutral"
#     source = "naver"
#     news_score = 50.0
#     is_disclosure = False


# class ThemeStrengthFactory(factory.Factory):
#     class Meta:
#         model = ThemeStrength
#
#     market = "KR"
#     theme = "AI"
#     strength_score = 75.0
#     news_count = 10
#     sentiment_avg = 0.5
