from spam.models import User
from dotenv import load_dotenv
load_dotenv()


users = User.query.with_entities(User.email).all()
users = list(map(lambda user: user[0], users))

print("\n".join(users))
