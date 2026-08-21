def analyze_business_opportunity(probabilities, model_classes, competition_summary):

    """Calculate a rule-based business opportunity assessment using historical ML performance and current competition."""
   # this fucntion receives three inputs, probabilities from predictor.py, model_classes from business_analyzer.py and competition_summary from competition.py. It calculates a final opportunity score based on historical performance and competition strength.

    class_probabilities = dict(zip(model_classes, probabilities))  #Convert probabilities into a dictionary, key is class and value is probability score
    high_probability = class_probabilities.get("High", 0)
    medium_probability = class_probabilities.get("Medium", 0)


    performance_score = high_probability * 100 + medium_probability * 50            #took full weight of high probability as it shows strongest signal

    competitor_count = competition_summary["competitor_count_retrieved"]
    avg_rating = competition_summary["avg_competitor_rating"]
    avg_reviews = competition_summary["avg_competitor_reviews"]
    high_rating_count = competition_summary["high_rating_competitors"]
    high_review_count = competition_summary["high_review_competitors"]


    if competitor_count > 0:
        competition_score = ((avg_rating / 5) * 40
                              + min(avg_reviews / 2000, 1) * 30 
                              + (high_rating_count / competitor_count) * 15 
                              + (high_review_count / competitor_count) * 15
                              )
    else:
        competition_score = 0


    opportunity_score = 0.60 * performance_score + 0.40 * (100 - competition_score)


    if performance_score < 40:
        performance_signal = "Weak historical performance"
    elif performance_score < 60:
        performance_signal = "Moderate historical performance"
    else:
        performance_signal = "Strong historical performance"



    if competition_score >= 70:
        competition_signal = "Strong competition"
    elif competition_score >= 40:
        competition_signal = "Moderate competition"
    else:
        competition_signal = "Limited competition"



    if opportunity_score < 40:
        opportunity_class = "Low"
    elif opportunity_score < 70:
        opportunity_class = "Moderate"
    else:
        opportunity_class = "High"


    return {
    "opportunity_score":{
        "score":round(float(opportunity_score), 2),
        "signal": opportunity_class
    },

    "historical_performance": {
        "score": round(float(performance_score), 2),
        "signal": performance_signal
    },

    "competition_strength": {
        "score": round(float(competition_score), 2),
        "signal": competition_signal
    }
}