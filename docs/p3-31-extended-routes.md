# P3-31 — Extended route duration

Ten shared-surface transfers proved insufficient to guarantee10s of traversal: P3-27 first robot approached the finish in2.4s and then waited. Add opt-in20/30/40transfer routes (version2), preserving all version1ten-transfer geometry exactly. Compute clone spacing from oriented cuboid bounds plus4m; grow visual ground if needed. CPU tests and actual40surface evaluation validate generated contact targets and runtime geometry. Frozen P3-28 model reaches around11transfers on40easy, then fails. New800update endurance fork learns the longer route. It remains separate from medium/hard dynamic jump objectives.

Motion accounting excludes final stance rocking from travel duration. A ten-second video alone is insufficient; no padding or artificial waiting is used to qualify the demo. Surface transfer count and actual jump count remain separate measurements.
