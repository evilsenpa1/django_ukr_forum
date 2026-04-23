# Utility for colored database name output in debug mode.
# Usage: call color_db_text() in settings.py under if DEBUG: block.
#
# class ColorTextConnettion_DB:
#     def color_db_text():
#         GREEN = "\033[92m"
#         YELLOW = "\033[93m"
#         RED = "\033[91m"
#         RESET = "\033[0m"
#         db_engine = DATABASES['default']['ENGINE']
#         db_name = DATABASES['default']['NAME']
#         color = YELLOW if 'sqlite' in db_engine else GREEN if 'postgresql' in db_engine else RED
#         if DEBUG:
#             print(f"\n{color}Active DB: {db_engine} ({db_name}){RESET}\n")
