drop table if exists form_questions;
create table form_questions (
  id int not null auto_increment
  , primary key (id)
)
;

drop table if exists form_answers;
create table form_answers (
  id int not null auto_increment
  , form_event_id int not null default 0
  , primary key (id)
)
;

drop table if exists form_event;
create table form_event (
  id int not null auto_increment
  , event_id varchar(16) not null default ''
  , form_id varchar(16) not null default ''
  , submitted_at datetime null
  , created_at datetime default current_timestamp
  , token varchar(128) null
  , primary key (id)
)
;

