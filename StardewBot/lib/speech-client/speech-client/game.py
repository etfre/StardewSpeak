import server

async def get_trees(location: str):
    trees = await server.request('GET_TREES', {"location": location})
    return trees
