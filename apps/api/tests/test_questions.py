"""Question endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_list_questions(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/start", headers=auth_headers)
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/questions", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_submit_answer(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/start", headers=auth_headers)
    qs = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/questions", headers=auth_headers)
    questions = qs.json()
    if questions:
        resp = await client.post(f"/api/v1/questions/{questions[0]['id']}/answer", json={"answer_text": "This is my test answer with relevant content."}, headers=auth_headers)
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_submit_answer_already_answered(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/start", headers=auth_headers)
    qs = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/questions", headers=auth_headers)
    questions = qs.json()
    if questions:
        qid = questions[0]["id"]
        await client.post(f"/api/v1/questions/{qid}/answer", json={"answer_text": "First answer"}, headers=auth_headers)
        resp = await client.post(f"/api/v1/questions/{qid}/answer", json={"answer_text": "Second answer"}, headers=auth_headers)
        assert resp.status_code == 404
