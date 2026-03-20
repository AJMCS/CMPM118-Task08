%~~~~~~~~~~~~~~~
% --- FACTS ---
%~~~~~~~~~~~~~~~


% ~Ghibli Movies~ (Title, Genre, Year).
movie(spirited_away, fantasy, 2001).
movie(my_neighbor_totoro, slice_of_life, 1988).
movie(princess_mononoke, action_adventure, 1997).
movie(howls_moving_castle, fantasy, 2004).
movie(kiki_delivery_service, slice_of_life, 1989).
movie(ponyo, fantasy, 2008).
movie(arrietty, slice_of_life, 2010).
movie(whisper_of_the_heart, slice_of_life, 1995).
movie(only_yesterday, drama, 1991).
movie(nausicaa_of_the_valley_of_the_wind, action_adventure, 1984).
movie(castle_in_the_sky, action_adventure, 1986).
movie(earthsea, fantasy, 2006).
movie(when_marnie_was_there, drama, 2014).
movie(the_boy_and_the_heron, fantasy, 2023).

% ~Movie Director~ (Movie, Director).
director(spirited_away, hayao_miyazaki).
director(my_neighbor_totoro, hayao_miyazaki).
director(princess_mononoke, hayao_miyazaki).
director(howls_moving_castle, hayao_miyazaki).
director(kiki_delivery_service, hayao_miyazaki).
director(ponyo, hayao_miyazaki).
director(arrietty, hiromasa_yonebayashi).
director(whisper_of_the_heart, yoshifumi_kondo).
director(only_yesterday, isao_takahata).
director(nausicaa_of_the_valley_of_the_wind, hayao_miyazaki).
director(castle_in_the_sky, hayao_miyazaki).
director(earthsea, goro_miyazaki).
director(when_marnie_was_there, hiromasa_yonebayashi).
director(the_boy_and_the_heron, hayao_miyazaki).

% ~Movie Composer~ (Movie, Composer).
composer(spirited_away, joe_hisaishi).
composer(my_neighbor_totoro, joe_hisaishi).
composer(princess_mononoke, joe_hisaishi).
composer(howls_moving_castle, joe_hisaishi).
composer(kiki_delivery_service, joe_hisaishi).
composer(ponyo, joe_hisaishi).
composer(arrietty, cecile_corbel).
composer(whisper_of_the_heart, yuji_nomi).
composer(only_yesterday, katsu_hoshi).
composer(nausicaa_of_the_valley_of_the_wind, joe_hisaishi).
composer(castle_in_the_sky, joe_hisaishi).
composer(earthsea, joe_hisaishi).
composer(when_marnie_was_there, joe_hisaishi).
composer(the_boy_and_the_heron, joe_hisaishi).

% ~Award Winning~ (Movie, Award).
award(spirited_away, academy_award_best_animated_feature).
award(the_boy_and_the_heron, academy_award_best_animated_feature).
award(spirited_away, japan_academy_prize_picture_of_the_year).
award(princess_mononoke, japan_academy_prize_picture_of_the_year).
award(spirited_away, golden_bear_berlin).

% ~Award Nomination~ (Movie, Nomination)
nomination(howls_moving_castle, academy_award_best_animated_feature).
nomination(the_wind_rises, academy_award_best_animated_feature).
nomination(tale_of_princess_kaguya, academy_award_best_animated_feature).
nomination(when_marnie_was_there, academy_award_best_animated_feature).
nomination(the_red_turtle, academy_award_best_animated_feature).
nomination(the_boy_and_the_heron, academy_award_best_animated_feature).


%~~~~~~~~~~~~~~~
% --- RULES ---
%~~~~~~~~~~~~~~~

watch_first(X) :- 
    award(X, _).

top_movies(X) :- 
    award(X, _); 
    nomination(X, _).

classic(X) :- 
    movie(X, _, Year), 
    Year < 2005,
    (award(X, _); nomination(X, _)).

modern_classic(X) :- 
    movie(X, _, Year), 
    Year >= 2015, 
    (award(X, _); nomination(X, _)).

same_director(X, Y) :- 
    director(X, Director), 
    director(Y, Director), 
    X \= Y.
    
same_composer(X, Y) :- 
    composer(X, Composer), 
    composer(Y, Composer), 
    X \= Y.

by_director(X, Director) :- 
    director(X, Director).

recommend_by_genre(X, Genre) :-
    movie(X, Genre, _).

recognized(X) :-
    award(X, _);
    nomination(X, _).

