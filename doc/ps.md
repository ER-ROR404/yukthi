YUKTHI 2026
NATIONAL-LEVEL HACKATHON
PROBLEM STATEMENT
Intelligent Energy & Equipment Monitoring
Build an intelligent system that learns equipment behaviour from operational data, detects meaningful abnormalities, and turns them into actionable insights.

- Background
  Modern buildings and facilities rely on energy-intensive equipment to maintain operational performance and occupant comfort. HVAC systems, chillers, pumps, fans, and related
  equipment continuously operate under changing environmental and operational conditions.
  The behaviour of such equipment is influenced by multiple factors, including equipment load, environmental conditions, operating conditions, time, and interactions between different
  measurements. Consequently, the same measurement value may represent normal operation under one condition but indicate abnormal behaviour under another.
  As equipment generates increasing volumes of operational and energy data, there is an opportunity to move beyond simple monitoring and fixed threshold-based alerts toward intelligent
  systems that can understand patterns of normal behaviour and identify conditions that require attention.
- The Problem
  Energy and equipment monitoring systems can provide large volumes of measurements, but identifying meaningful abnormal behaviour from these measurements remains a challenging task.
  Equipment does not operate under a single fixed condition. Its energy consumption and operational behaviour can change with factors such as building load, cooling conditions, outside
  temperature, humidity, and other environmental or contextual variables. Therefore, a simple threshold or isolated measurement may not be sufficient to determine whether equipment is
  actually behaving abnormally.
  The challenge is to develop a system that can learn from historical operational data and distinguish meaningful deviations from expected behaviour from normal variations in equipment
  operation.
  The system should help answer questions such as:
- What is happening with the equipment?
- Is the observed behaviour normal for the given operating conditions?
- Which equipment or time periods require attention?
- How significant is the detected condition?
- What evidence supports the identified issue?
- What action or investigation should be considered?
- Challenge Objective
  Develop a full-stack, machine-learning-driven application that analyses historical equipment, energy, environmental, and operational data to identify abnormal behaviour and translate
  those findings into understandable and actionable operational insights.
  The solution should go beyond simply displaying measurements. Machine learning should make a meaningful contribution to identifying or interpreting equipment behaviour.
  The objective is to transform operational data into intelligence that supports equipment monitoring, operational decision-making, and improved energy awareness.
- Scope of the Challenge
  Core Capability
  The fundamental capability expected from the solution is contextual anomaly detection.
  The system should establish an understanding of expected equipment behaviour under relevant operating and environmental conditions, and identify meaningful deviations from that
  expected behaviour.
- Normal behaviour can vary over time.
- Equipment operates under different loads and conditions.
- Multiple variables may need to be considered together.
- Isolated deviations may not necessarily indicate an issue.
- Persistent, repeated, or contextual deviations may require greater attention.
  Extended Capabilities
  Teams may extend their solutions to provide additional intelligence where supported by their approach and the available data.
- Equipment health assessment
- Progressive degradation detection
- Identification of recurring or persistent abnormal behaviour
- Likely equipment issue or fault identification, where supported by the available data
- Severity or risk assessment
- Prioritization of conditions requiring attention
- Evidence-based operational recommendations
  Where the available measurements do not support identification of a specific physical fault, teams may instead identify the abnormal behaviour, its contributing factors, and the
  operational condition that warrants investigation.
  Teams are not required to implement every capability listed above. The quality and usefulness of the capabilities implemented are more important than the number of features.
- Expected Solution
  A strong solution should connect data processing, machine-learning analysis, and user-facing intelligence into a coherent end-to-end workflow.
  Operational Data -> Data Processing -> ML Analysis -> Anomaly/Health Assessment -> Actionable Insight -> Interpretation
  The solution should be designed as a reusable data-to-insight pipeline capable of processing datasets that conform to the provided Data Specification, rather than relying on hard-coded
  observations or dataset-specific assumptions.
  The application should be capable of:
- Processing the provided historical data.
- Understanding relevant equipment and contextual behaviour.
- Applying an appropriate machine-learning approach.
- Detecting meaningful abnormal behaviour.
- Presenting the affected equipment and relevant observations.
- Providing appropriate interpretation of detected conditions.
- Communicating severity, risk, or priority where applicable.
- Supporting the user with evidence-based insights or recommendations.
  The implementation approach is open to participants. Different machine-learning methodologies may be appropriate depending on how teams formulate the problem and use the available data.
- Data
  Teams will be provided with historical operational data from multiple chiller units, representing equipment operation, energy consumption, and environmental conditions.
  The dataset includes measurements relating to:
- Equipment identity and time
- Chilled-water flow
- Cooling-water temperature
- Building load
- Chiller energy consumption
- Outside temperature
- Dew point
- Humidity
- Wind speed
- Atmospheric pressure
  Detailed information regarding the dataset schema, units, timestamps, variables, missing values, and their interpretation is provided separately in the Data Specification.
  Teams should use the Data Specification as the data contract for designing their ingestion, preprocessing, and analysis pipeline.
- Machine Learning Requirement
  Machine learning must be a meaningful component of the solution.
  The ML component should materially contribute to the identification, assessment, or interpretation of equipment behaviour.
  Solutions based solely on fixed thresholds, static rules, or simple visualization without meaningful ML contribution do not address the core intelligence requirement of the
  challenge.
  Teams are free to select and justify the machine-learning methodology they consider appropriate for the problem. The choice of algorithm is not prescribed.
- Application Requirement
  The submission should be a functional software application rather than only a trained model, notebook, or static visualization.
  The application should provide a usable interface through which a user can explore equipment behaviour and understand the intelligence produced by the solution.
  Depending on the approach taken, this may include:
- Equipment-level monitoring
- Time-series exploration
- Anomaly identification
- Historical comparisons
- Severity or health indicators
- Investigation of abnormal periods
- Supporting evidence for detected conditions
- Operational recommendations
  The application should demonstrate a clear relationship between the underlying data, the ML analysis, and the information presented to the user.
- Technology Freedom
  Teams have complete freedom to select the technologies used to develop their solution.
- Programming language
- Machine-learning algorithm
- Development framework
- Database
- Visualization library
- Cloud platform
- Deployment platform
  Participants should select technologies appropriate to their solution and be able to explain their technical decisions.
- Constraints
  The challenge is designed for an 18-hour hackathon. Solutions should therefore balance technical sophistication with practical implementation.
  The solution must:
- Operate on datasets that conform to the provided Data Specification and not depend on hard-coded observations or dataset-specific assumptions.
- Provide a functional application.
- Include a meaningful machine-learning component.
- Demonstrate an end-to-end workflow.
- Provide insights that can be understood and investigated by a user.
- Support conclusions and recommendations with appropriate evidence from the data and the implemented methodology.
  Teams should not assume that a complex architecture or large number of technologies necessarily produces a better solution.
- Expected Impact
  An effective intelligent monitoring system could help organizations move from reactive monitoring toward more informed operational decision-making.
- Earlier identification of abnormal equipment behaviour
- Improved visibility into energy performance
- Identification of conditions that may warrant investigation
- Better prioritization of operational issues
- Support for equipment health and degradation monitoring
- Potential reduction in unnecessary energy consumption
- More informed maintenance and operational decisions
- Reduced risk of prolonged equipment issues and associated downtime
  These represent potential applications of the proposed systems; the actual value depends on the quality, reliability, and applicability of the solution developed.
- Challenge Outcome
  The objective of YUKTHI 2026 is not simply to build another dashboard for displaying equipment measurements.
  The challenge is to transform historical operational data into usable intelligence.
  "What are the measurements?" should become "What is unusual, why might it matter, and what should be investigated?"
  DETECT. UNDERSTAND. ASSESS. ACT.
