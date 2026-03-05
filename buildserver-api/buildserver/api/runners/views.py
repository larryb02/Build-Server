from fastapi import APIRouter

router = APIRouter(prefix="/runners")


@router.post("/register")
def register_runner():
    # generate token --
    # should expire if not used within say 30 minutes
    return {}
