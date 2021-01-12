from spam.models import User
from dotenv import load_dotenv

load_dotenv()

# we get all the users and we print one user per line
users = User.query.with_entities(User.email).all()
users = list(map(lambda user: user[0], users))

print("\n".join(users))
