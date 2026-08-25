-- Correct a fabricated hybrid Bobzien citation in the applied consensus seed.
-- The 2013 article concerns Aristotle EN III.5 and does not discuss Origen.

SET search_path TO free_will, public;

UPDATE free_will.scholarly_consensus_topics
SET positions = jsonb_set(
        jsonb_set(
            positions,
            '{1,citation}',
            to_jsonb(
                'Bobzien, S. 1998. "The Inadvertent Conception and Late Birth of the Free-Will Problem." Phronesis 43: 133-175.'::text
            ),
            false
        ),
        '{1,summary}',
        to_jsonb(
            'Bobzien reconstructs the explicit free-will problem as a late ancient development. Her historical method supports separating ancient vocabulary and arguments from modern libertarian taxonomies, but this article does not itself settle Origen''s position.'::text
        ),
        false
    ),
    updated_at = now()
WHERE topic_slug = 'origen_libertarian_label_anachronism'
  AND positions->1->>'citation' =
      'Bobzien, S. 2014. "Found in Translation: Aristotle''s Nicomachean Ethics III.1-5 on Voluntariness and Free Decision." Phronesis 59: 369-417.';
