using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.TerrainFeatures;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using xTile.ObjectModel;
using xTile.Tiles;

namespace StardewSpeak.Pathfinder
{
	public class Location
	{
		public int X;
		public int Y;
		public int F;
		public int G;
		public int H;
		public Location Parent;
		public bool Preferable = false;
	}

	public class Point2
	{
		public int X;
		public int Y;

		public Point2(int x, int y)
		{
			this.X = x;
			this.Y = y;
		}
	}

	public class Pathfinder
	{

		private static readonly sbyte[,] Directions = new sbyte[4, 2]
			{
				{
					-1,
					0
				},
				{
					1,
					0
				},
				{
					0,
					1
				},
				{
					0,
					-1
				}
			};
		private static PriorityQueue _openList = new PriorityQueue();
		private static HashSet<int> _closedList = new HashSet<int>();
		private static int _counter = 0;
		public delegate bool isAtEnd(PathNode currentNode, Point endPoint, GameLocation location, Character c);
		public delegate bool adjustTileScore(PathNode currentNode, Point endPoint, GameLocation location, Character c);
		public static dynamic FindPath(GameLocation location, int startX, int startY, int targetX, int targetY, int limit = -1)
		{
			var startPoint = new Point(startX, startY);
			var endPoint = new Point(targetX, targetY);
			var path = findPath(startPoint, endPoint, PathFindController.isAtEndPoint, location, limit);
			return path?.Select(p => new { p.X, p.Y }).ToList();
		}

		public static Stack<Point> findPath(Point startPoint, Point endPoint, isAtEnd endPointFunction, GameLocation location, int limit = -1)
		{
			if (Interlocked.Increment(ref _counter) != 1)
			{
				throw new Exception();
			}
			try
			{
				_openList.Clear();
				_closedList.Clear();
				PriorityQueue openList = _openList;
				HashSet<int> closedList = _closedList;
				int iterations = 0;
				openList.Enqueue(new PathNode(startPoint.X, startPoint.Y, 0, null), Math.Abs(endPoint.X - startPoint.X) + Math.Abs(endPoint.Y - startPoint.Y));
				int layerWidth = location.map.Layers[0].LayerWidth;
				int layerHeight = location.map.Layers[0].LayerHeight;
				bool isFarmer = true;
				Character character = Game1.player;
				while (!openList.IsEmpty())
				{
					PathNode currentNode = openList.Dequeue();
					if (endPointFunction(currentNode, endPoint, location, character))
					{
						return reconstructPath(currentNode);
					}
					closedList.Add(currentNode.id);
					int ng = (byte)(currentNode.g + 1);
					for (int i = 0; i < 4; i++)
					{
						int nx = currentNode.x + Directions[i, 0];
						int ny = currentNode.y + Directions[i, 1];
						int nid = PathNode.ComputeHash(nx, ny);
						if (!closedList.Contains(nid))
						{
							if ((nx != endPoint.X || ny != endPoint.Y) && (nx < 0 || ny < 0 || nx >= layerWidth || ny >= layerHeight))
							{
								closedList.Add(nid);
							}
							else
							{
								PathNode neighbor = new PathNode(nx, ny, currentNode);
								neighbor.g = (byte)(currentNode.g + 1);
								if (location.isCollidingPosition(new Rectangle(neighbor.x * 64 + 1, neighbor.y * 64 + 1, 62, 62), Game1.viewport, isFarmer, 0, glider: false, character, pathfinding: true))
								{
									closedList.Add(nid);
								}
								else
								{
									int f = ng + (Math.Abs(endPoint.X - nx) + Math.Abs(endPoint.Y - ny));
									closedList.Add(nid);
									openList.Enqueue(neighbor, f);
								}
							}
						}
					}
					if (limit >= 0)
					{
						iterations++;
						if (iterations >= limit)
						{
							return null;
						}
					}
				}
				return null;
			}
			finally
			{
				if (Interlocked.Decrement(ref _counter) != 0)
				{
					throw new Exception();
				}
			}
		}

		public static Stack<Point> reconstructPath(PathNode finalNode)
		{
			Stack<Point> path = new Stack<Point>();
			path.Push(new Point(finalNode.x, finalNode.y));
			for (PathNode walk = finalNode.parent; walk != null; walk = walk.parent)
			{
				path.Push(new Point(walk.x, walk.y));
			}
			return path;
		}

	}
}