# What this tests ?
## Tests /chat/completions by generating a key and then making a chat completions request
import pytest
import asyncio
import aiohttp, openai
from openai import OpenAI


def response_header_check(response):
    """
    - assert if response headers < 4kb (nginx limit).
    """
    headers_size = sum(len(k) + len(v) for k, v in response.raw_headers)
    assert headers_size < 4096, "Response headers exceed the 4kb limit"


async def generate_key(session):
    url = "http://0.0.0.0:4000/key/generate"
    headers = {"Authorization": "Bearer sk-1234", "Content-Type": "application/json"}
    data = {
        "models": [
            "gpt-4",
            "text-embedding-ada-002",
            "dall-e-2",
            "fake-openai-endpoint-2",
        ],
        "duration": None,
    }

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status
        response_text = await response.text()

        print(response_text)
        print()

        if status != 200:
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers

        return await response.json()


async def new_user(session):
    url = "http://0.0.0.0:4000/user/new"
    headers = {"Authorization": "Bearer sk-1234", "Content-Type": "application/json"}
    data = {
        "models": ["gpt-4", "text-embedding-ada-002", "dall-e-2"],
        "duration": None,
    }

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status
        response_text = await response.text()

        print(response_text)
        print()

        if status != 200:
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers
        return await response.json()


async def chat_completion(session, key, model="gpt-4"):
    url = "http://0.0.0.0:4000/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
    }

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status
        response_text = await response.text()

        print(response_text)
        print()

        if status != 200:
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers

        return await response.json()


async def completion(session, key):
    url = "http://0.0.0.0:4000/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {"model": "gpt-4", "prompt": "Hello!"}

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status

        if status != 200:
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers

        response = await response.json()

        return response


async def embeddings(session, key):
    url = "http://0.0.0.0:4000/embeddings"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "text-embedding-ada-002",
        "input": ["hello world"],
    }

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status
        response_text = await response.text()

        print(response_text)

        if status != 200:
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers


async def image_generation(session, key):
    url = "http://0.0.0.0:4000/images/generations"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "dall-e-2",
        "prompt": "A cute baby sea otter",
    }

    async with session.post(url, headers=headers, json=data) as response:
        status = response.status
        response_text = await response.text()

        print(response_text)
        print()

        if status != 200:
            if (
                "Connection error" in response_text
            ):  # OpenAI endpoint returns a connection error
                return
            raise Exception(f"Request did not return a 200 status code: {status}")

        response_header_check(
            response
        )  # calling the function to check response headers


@pytest.mark.asyncio
async def test_chat_completion():
    """
    - Create key
    Make chat completion call
    - Create user
    make chat completion call
    """
    async with aiohttp.ClientSession() as session:
        key_gen = await generate_key(session=session)
        key = key_gen["key"]
        await chat_completion(session=session, key=key)
        key_gen = await new_user(session=session)
        key_2 = key_gen["key"]
        await chat_completion(session=session, key=key_2)


# @pytest.mark.skip(reason="Local test. Proxy not concurrency safe yet. WIP.")
@pytest.mark.asyncio
async def test_chat_completion_ratelimit():
    """
    - call model with rpm 1
    - make 2 parallel calls
    - make sure 1 fails
    """
    async with aiohttp.ClientSession() as session:
        # key_gen = await generate_key(session=session)
        key = "sk-1234"
        tasks = []
        tasks.append(
            chat_completion(session=session, key=key, model="fake-openai-endpoint-2")
        )
        tasks.append(
            chat_completion(session=session, key=key, model="fake-openai-endpoint-2")
        )
        try:
            await asyncio.gather(*tasks)
            pytest.fail("Expected at least 1 call to fail")
        except Exception as e:
            pass


@pytest.mark.asyncio
async def test_chat_completion_old_key():
    """
    Production test for backwards compatibility. Test db against a pre-generated (old key)
    - Create key
    Make chat completion call
    """
    async with aiohttp.ClientSession() as session:
        try:
            key = "sk-ecMXHujzUtKCvHcwacdaTw"
            await chat_completion(session=session, key=key)
        except Exception as e:
            key = "sk-ecMXHujzUtKCvHcwacdaTw"  # try diff db key (in case db url is for the other db)
            await chat_completion(session=session, key=key)


@pytest.mark.asyncio
async def test_completion():
    """
    - Create key
    Make chat completion call
    - Create user
    make chat completion call
    """
    async with aiohttp.ClientSession() as session:
        key_gen = await generate_key(session=session)
        key = key_gen["key"]
        await completion(session=session, key=key)
        key_gen = await new_user(session=session)
        key_2 = key_gen["key"]
        # response = await completion(session=session, key=key_2)

    ## validate openai format ##
    client = OpenAI(api_key=key_2, base_url="http://0.0.0.0:4000")

    client.completions.create(
        model="gpt-4",
        prompt="Say this is a test",
        max_tokens=7,
        temperature=0,
    )


@pytest.mark.asyncio
async def test_embeddings():
    """
    - Create key
    Make embeddings call
    - Create user
    make embeddings call
    """
    async with aiohttp.ClientSession() as session:
        key_gen = await generate_key(session=session)
        key = key_gen["key"]
        await embeddings(session=session, key=key)
        key_gen = await new_user(session=session)
        key_2 = key_gen["key"]
        await embeddings(session=session, key=key_2)


@pytest.mark.asyncio
async def test_image_generation():
    """
    - Create key
    Make embeddings call
    - Create user
    make embeddings call
    """
    async with aiohttp.ClientSession() as session:
        key_gen = await generate_key(session=session)
        key = key_gen["key"]
        await image_generation(session=session, key=key)
        key_gen = await new_user(session=session)
        key_2 = key_gen["key"]
        await image_generation(session=session, key=key_2)
