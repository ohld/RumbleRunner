from app.api.command_list import CallbackId, PendingRequestId
from app.core.game_ranking import GameRankingHelpers
from app.core.player import PlayerHelpers
from app.core.trueskill import TrueSkillParams
from app.models.all import Player
from base.api.handler import Context, InlineMenu, InlineMenuButton
from base.api.routing import Requests


class PlayerHandlers:
    @staticmethod
    def build_players_menu(context: Context):
        menu = []
        game_ranking = GameRankingHelpers.get_or_create(context)
        players = PlayerHelpers.get_for_ranking(context)
        for player in players:
            menu.append([InlineMenuButton(player.name, CallbackId.TS_PLAYER_OPEN_MENU, player.id)])
        menu.append([InlineMenuButton('New player..', CallbackId.TS_PLAYERS_MANAGEMENT_START_PLAYER_CREATION)])
        menu.append([InlineMenuButton('Back', CallbackId.TS_RANKING_OPEN_MENU)])
        return InlineMenu(menu, user_tg_id=context.sender.tg_id)

    @staticmethod
    def build_player_menu(context: Context, player_id: int):
        return InlineMenu([
            [InlineMenuButton('Rename..', CallbackId.TS_PLAYER_START_RENAMING, str(player_id))],
            [
                InlineMenuButton('Reset ranking stats', CallbackId.TS_PLAYER_RESET_SCORE, str(player_id)),
                InlineMenuButton('Delete forever', CallbackId.TS_PLAYER_DELETE, str(player_id))
            ],
            [InlineMenuButton('Back', CallbackId.TS_PLAYERS_MANAGEMENT_OPEN_MENU)]
        ])

    @staticmethod
    def management_open_menu(context: Context):
        context.actions.edit_message('Our heroes:')
        context.actions.edit_markup(PlayerHandlers.build_players_menu(context))

    @staticmethod
    def start_player_creation(context: Context):
        Requests.replace(context, PendingRequestId.TS_PLAYERS_MANAGEMENT_PLAYER_CREATION_NAME)
        context.actions.edit_message('Write name for the new player')
        context.actions.edit_markup(
            InlineMenu([[InlineMenuButton('Cancel', CallbackId.TS_PLAYERS_MANAGEMENT_CANCEL_PLAYER_CREATION)]],
                       user_tg_id=context.sender.tg_id))

    @staticmethod
    def player_creation_name(context: Context):
        new_name = context.data.text.strip()
        if not new_name:
            return 'Empty name? Try again'
        game_ranking = GameRankingHelpers.get_or_create(context)
        context.session.add(Player(name=new_name, mu=TrueSkillParams.DEFAULT_MU, sigma=TrueSkillParams.DEFAULT_SIGMA,
                                   game_ranking_id=game_ranking.id))
        context.session.commit()
        context.actions.msg_id = context.pending_request.original_message_id
        context.session.delete(context.pending_request)
        PlayerHandlers.management_open_menu(context)

    @staticmethod
    def cancel_player_creation(context: Context):
        pending_request = Requests.get(context)
        if pending_request:
            context.session.delete(pending_request)
        PlayerHandlers.management_open_menu(context)

    @staticmethod
    def open_menu(context: Context, player_id=None):
        if player_id is None:
            player_id = context.data.callback_data.data
        player = context.session.query(Player).filter(Player.id == player_id).one_or_none()
        if player is None:
            PlayerHandlers.management_open_menu(context)
            return

        skill_confidence = 1.0 - player.sigma / (TrueSkillParams.DEFAULT_SIGMA * 2)
        context.actions.edit_message('Howdy, {}?\n\nMatches played: {}\nSkill confidence: {}%'.format(
            player.name, len(player.participations), int(skill_confidence * 100.0)))
        context.actions.edit_markup(PlayerHandlers.build_player_menu(context, player_id))

    @staticmethod
    def start_renaming(context: Context):
        player = context.session.query(Player).filter(Player.id == context.data.callback_data.data).one_or_none()
        if player:
            Requests.replace(context, PendingRequestId.TS_PLAYER_RENAMING_NAME, str(player.id))
            context.actions.edit_message('Write new name for the {}:'.format(player.name))
            context.actions.edit_markup(InlineMenu([[InlineMenuButton('Cancel', CallbackId.TS_CANCEL_PLAYER_RENAMING)]],
                                                   user_tg_id=context.sender.tg_id))
        else:
            context.actions.edit_markup(PlayerHandlers.open_menu(context))

    @staticmethod
    def renaming_name(context: Context):
        new_name = context.data.text.strip()
        if not new_name:
            return 'Empty name? Try again'
        player_id = context.pending_request.additional_data
        player = context.session.query(Player).filter(Player.id == player_id).one_or_none()
        if player:
            player.name = new_name
            context.session.commit()
        context.actions.msg_id = context.pending_request.original_message_id
        context.session.delete(context.pending_request)
        PlayerHandlers.open_menu(context, player_id)

    @staticmethod
    def cancel_renaming(context: Context):
        pending_request = Requests.get(context)
        player_id = context.pending_request.additional_data
        if pending_request:
            context.session.delete(pending_request)
        PlayerHandlers.open_menu(context, player_id)

    @staticmethod
    def reset_score(context: Context):
        player = context.session.query(Player).filter(Player.id == context.data.callback_data.data).one_or_none()
        if player:
            player.mu = TrueSkillParams.DEFAULT_MU
            player.sigma = TrueSkillParams.DEFAULT_SIGMA
        PlayerHandlers.open_menu(context)

    @staticmethod
    def delete(context: Context):
        player = context.session.query(Player).filter(Player.id == context.data.callback_data.data).one_or_none()
        if player:
            context.session.delete(player)
            context.session.commit()
            PlayerHandlers.management_open_menu(context)
