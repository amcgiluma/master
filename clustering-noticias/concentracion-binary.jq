(
  ["seed", "group", "majority_topic", "term", "df", "idf", "in_group",
   "group_size", "outside", "outside_size", "difference_pp"],
  (.documents as $n
   | .results.Binary.runs | to_entries[] | (.key | tonumber) as $seed
   | .value.groups[] as $group
   | $group.terms | map(select(.term == "government" or .term == "people"))
   | sort_by(.term)[]
   | [$seed, $group.group, ($group.topics | to_entries | max_by(.value).key),
      .term, .df, .idf, .in_group, $group.size, .outside, ($n - $group.size),
      (.difference * 100)])
) | @csv
