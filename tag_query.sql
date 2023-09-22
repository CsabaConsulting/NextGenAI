SELECT image_id FROM `gdg-demos.images.images` WHERE datetime BETWEEN '2023-09-19' AND '2023-09-20';

SELECT DISTINCT(tg.tag) FROM `gdg-demos.images.images` AS im
JOIN `gdg-demos.images.tags` AS tg ON im.image_id = tg.image_id
WHERE datetime BETWEEN '2023-09-19' AND '2023-09-20' ORDER BY tg.tag;
