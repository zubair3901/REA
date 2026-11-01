"""Shared category validation; new categories require explicit local labor rates."""
from typing import Literal
RoomCategory = Literal['living','bedroom','kitchen','bathroom','restaurant','garden','exterior','landscape','office','dining']
PRIORITIES = {
 'living':['seating','table','lighting','rug','decor'],
 'bedroom':['bed','table','lighting','seating','rug','decor'],
 'office':['desk','seating','lighting','table','decor'],
 'kitchen':['storage','table','seating','lighting','decor'],
 'bathroom':['storage','lighting','decor','textiles'],
 'restaurant':['table','seating','lighting','decor','storage'],
 'garden':['seating','table','lighting','decor'],
 'exterior':['lighting','seating','decor'],
 'landscape':['seating','lighting','decor','table'],
 'dining':['table','seating','lighting','rug','decor'],
}
