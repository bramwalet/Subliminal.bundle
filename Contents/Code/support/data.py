# coding=utf-8


def migrate():
    """
    some Dict/Data migrations here, no need for a more in-depth migration path for now
    :return:
    """

    # migrate subtitle history from Dict to Data
    if "history" in Dict and Dict["history"]["history_items"]:
        Log.Debug("Running migration for history data")
        from support.history import get_history
        history = get_history()

        for item in reversed(Dict["history"]["history_items"]):
            history.add(item.item_title, item.rating_key, item.section_title, subtitle=item.subtitle, mode=item.mode,
                        time=item.time)

        del Dict["history"]
        Dict.Save()
