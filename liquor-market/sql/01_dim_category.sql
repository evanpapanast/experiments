-- Product families: 44 detailed ABD categories grouped into 11 simple families (reviewed by hand).
CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.liquor_market.dim_category` AS
SELECT category_name, family
FROM UNNEST(ARRAY<STRUCT<category_name STRING, family STRING>>[
  ('AMERICAN VODKAS', 'Vodka'), ('IMPORTED VODKAS', 'Vodka'), ('AMERICAN FLAVORED VODKA', 'Vodka'),
  ('IMPORTED FLAVORED VODKA', 'Vodka'), ('NEUTRAL GRAIN SPIRITS', 'Vodka'), ('NEUTRAL GRAIN SPIRITS FLAVORED', 'Vodka'),
  ('STRAIGHT BOURBON WHISKIES', 'American whiskey'), ('TENNESSEE WHISKIES', 'American whiskey'),
  ('BLENDED WHISKIES', 'American whiskey'), ('STRAIGHT RYE WHISKIES', 'American whiskey'),
  ('SINGLE BARREL BOURBON WHISKIES', 'American whiskey'), ('BOTTLED IN BOND BOURBON', 'American whiskey'),
  ('CORN WHISKIES', 'American whiskey'), ('IOWA DISTILLERY WHISKIES', 'American whiskey'), ('AMERICAN WHISKIES', 'American whiskey'),
  ('CANADIAN WHISKIES', 'Canadian whisky'),
  ('SCOTCH WHISKIES', 'Scotch & Irish whisky'), ('SINGLE MALT SCOTCH', 'Scotch & Irish whisky'),
  ('IRISH WHISKIES', 'Scotch & Irish whisky'), ('IMPORTED WHISKIES', 'Scotch & Irish whisky'),
  ('100% AGAVE TEQUILA', 'Tequila & mezcal'), ('MIXTO TEQUILA', 'Tequila & mezcal'), ('MEZCAL', 'Tequila & mezcal'),
  ('SPICED RUM', 'Rum'), ('FLAVORED RUM', 'Rum'), ('WHITE RUM', 'Rum'), ('GOLD RUM', 'Rum'), ('AGED DARK RUM', 'Rum'),
  ('WHISKEY LIQUEUR', 'Liqueurs & schnapps'), ('IMPORTED CORDIALS & LIQUEURS', 'Liqueurs & schnapps'),
  ('CREAM LIQUEURS', 'Liqueurs & schnapps'), ('AMERICAN SCHNAPPS', 'Liqueurs & schnapps'),
  ('IMPORTED SCHNAPPS', 'Liqueurs & schnapps'), ('AMERICAN CORDIALS & LIQUEURS', 'Liqueurs & schnapps'),
  ('COFFEE LIQUEURS', 'Liqueurs & schnapps'), ('TRIPLE SEC', 'Liqueurs & schnapps'),
  ('IMPORTED BRANDIES', 'Brandy'), ('AMERICAN BRANDIES', 'Brandy'),
  ('IMPORTED DRY GINS', 'Gin'), ('AMERICAN DRY GINS', 'Gin'), ('FLAVORED GIN', 'Gin'), ('AMERICAN SLOE GINS', 'Gin'),
  ('IMPORTED GINS', 'Gin'),
  ('COCKTAILS/RTD', 'Ready-to-drink cocktails'),
  ('TEMPORARY & SPECIALTY PACKAGES', 'Gift packs & other'), ('SPECIAL ORDER ITEMS', 'Gift packs & other'),
  ('IMPORTED DISTILLED SPIRITS SPECIALTY', 'Gift packs & other'), ('AMERICAN DISTILLED SPIRITS SPECIALTY', 'Gift packs & other'),
  ('DISTILLED SPIRITS SPECIALTY', 'Gift packs & other'), ('IOWA DISTILLERIES', 'Gift packs & other'),
  ('HOLIDAY VAP', 'Gift packs & other'), ('DELISTED / SPECIAL ORDER ITEMS', 'Gift packs & other')
])
