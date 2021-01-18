# import asyncio
# import traceback
# import directinput

# class ObjectiveFailedError(BaseException):
#     pass


# class Objective:
#     async def run(self):
#         raise NotImplementedError

#     async def wrap_run(self):
#         self.full_task = asyncio.create_task(self.run_and_cancel())
#         await self.full_task

#     async def run_and_cancel(self):
#         name = self.__class__.__name__
#         server.log(f"Starting objective {name}")
#         self.run_task = asyncio.create_task(self.run())
#         try:
#             await self.run_task
#         except (Exception, ObjectiveFailedError) as e:
#             err = e
#             tb = traceback.format_exc()
#             server.log(f"Objective {name} errored: \n{tb}")
#         except asyncio.CancelledError as e:
#             err = e
#             server.log(f"Canceling objective {name}")
#         else:
#             err = None
#             server.log(f"Successfully completed objective {name}")
#         await self.cleanup(err)

#     async def cleanup(self, exception):
#         pass

#     def fail(self, msg=None):
#         if msg is None:
#             msg = "Objective {self.__class__.__name__} failed"
#         raise ObjectiveFailedError(msg)


# class HoldKeyObjective(Objective):
#     def __init__(self, keys):
#         self.keys = keys

#     async def run(self):
#         for k in self.keys:
#             directinput.press(k)
#         # infinite loop to indicate that the objective isn't done until task is canceled
#         await sleep_forever()

#     async def cleanup(self, exception):
#         for k in self.keys[::-1]:
#             directinput.release(k)


# class FaceDirectionObjective(Objective):
#     def __init__(self, direction):
#         self.direction = direction

#     async def run(self):
#         async with server.player_status_stream() as stream:
#             await face_direction(self.direction, stream)


# class MoveNTilesObjective(Objective):
#     def __init__(self, direction, n):
#         self.direction = direction
#         self.n = n

#     async def run(self):
#         async with server.player_status_stream(ticks=1) as stream:
#             status = await stream.current()
#             await ensure_not_moving(stream)
#             from_x, from_y = status["tileX"], status["tileY"]
#             to_x, to_y = from_x, from_y
#             if self.direction == "north":
#                 to_y -= self.n
#             elif self.direction == "east":
#                 to_x += self.n
#             elif self.direction == "south":
#                 to_y += self.n
#             elif self.direction == "west":
#                 to_x -= self.n
#             else:
#                 raise ValueError(f"Unexpected direction {self.direction}")
#             path = await path_to_position(to_x, to_y)
#             server.log(path.tiles)
#             await pathfind_to_position(path, status['location'], stream)

#     async def cleanup(self, exception):
#         if exception:
#             async with server.player_status_stream() as stream:
#                 await ensure_not_moving(stream)


# class MoveToLocationObjective(Objective):
#     # def __init__(self, x, y, location):
#     def __init__(self):
#         x, y, location = 68, 17, "Farm"
#         self.x = x
#         self.y = y
#         self.location = location

#     async def run(self):
#         async with server.player_status_stream() as stream:
#             await ensure_not_moving(stream)
#             route = await request_route(self.location, self.x, self.y)
#             for i, location in enumerate(route[:-1]):
#                 next_location = route[i + 1]
#                 server.log(f"Getting path to next location {next_location}")
#                 path = await path_to_warp(next_location)
#                 await pathfind_to_warp(path, location, next_location, stream)

#             path = await path_to_position(self.x, self.y)
#             await pathfind_to_position(path, route[-1], stream)

#     async def cleanup(self, exception):
#         if exception:
#             async with server.player_status_stream() as stream:
#                 await ensure_not_moving(stream)

