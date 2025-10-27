import asyncio
from unittest.mock import MagicMock
from apps.knowledge_builder.coverage.meter import CoverageMeterService


class FakeSession:
    async def __aenter__(self):
        print("Entering session")
        return self

    async def __aexit__(self, *args):
        print("Exiting session")
        pass

    async def execute(self, query):
        print(f"Executing query")
        result = MagicMock()
        result.scalar.return_value = 5
        return result


def fake_factory():
    return FakeSession()


async def main():
    service = CoverageMeterService(session_factory=fake_factory)
    print("Service created")

    metrics = await service.calculate_coverage(
        taxonomy_version="1.0.0",
        node_ids=["node1"]
    )
    print(f"Metrics: {metrics}")

if __name__ == "__main__":
    asyncio.run(main())
