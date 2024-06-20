
from typing import Dict, List, Optional, Union

from opencompass.utils.prompt import PromptList

from opencompass.models.base_api import BaseAPIModel

PromptType = Union[PromptList, str]

import time

import websocket
import json
from functools import partial

class XunFei(BaseAPIModel):
    """Model wrapper around XunFei.

    Args:
        path (str): Provided URL.
        appid (str): Provided APPID.
        api_secret (str): Provided APISecret.
        api_key (str): Provided APIKey.
        domain (str): Target version domain. Defaults to `general`.
        query_per_second (int): The maximum queries allowed per second
            between two consecutive calls of the API. Defaults to 2.
        max_seq_len (int): Unused here.
        meta_template (Dict, optional): The model's meta prompt
            template if needed, in case the requirement of injecting or
            wrapping of any meta instructions.
        retry (int): Number of retires if the API call fails. Defaults to 2.
    """

    def __init__(self,
                 path: str,
                 query_per_second: int = 2,
                 max_seq_len: int = 4096,
                 meta_template: Optional[Dict] = None,
                 retry: int = 2):
        super().__init__(path=path,
                         max_seq_len=max_seq_len,
                         query_per_second=query_per_second,
                         meta_template=meta_template,
                         retry=retry)


        from urllib.parse import urlencode, urlparse

        self.urlencode = urlencode
        self.websocket = websocket
        self.websocket.enableTrace(False)




    def generate(
        self,
        inputs: List[PromptType],
        max_out_len: int = 512,
    ) -> List[str]:
        """Generate results given a list of inputs.

        Args:
            inputs (List[PromptType]): A list of strings or PromptDicts.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            List[str]: A list of generated strings.
        """
        '''
        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(self._generate, inputs,
                             [max_out_len] * len(inputs)))
        self.flush()
        return results
        '''
        results = []
        for input_i in inputs:
            result = self._generate(input_i, max_out_len)
            time.sleep(0.2)
            results.append(result)

        return results

    def _generate(
        self,
        input: PromptType,
        max_out_len: int = 4096,
    ) -> str:
        """Generate results given an input.

        Args:
            inputs (PromptType): A string or PromptDict.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            str: The generated string.
        """
        assert isinstance(input, (str, PromptList))

        # FIXME: messages only contains the last input

        global final_result
        final_result = ''

        def on_message(ws, message):
            # print("Received message:")
            global final_result
            reply = json.loads(message)
            select_reply = reply["payload"]["choices"]["text"][0]["content"]
            return_reply = select_reply.replace('<ret><ret>', '\n').replace('<ret>', '')
            # print(type(return_reply))
            # print(str(return_reply))
            # global final_result
            final_result += return_reply

        '''
        def get_final_result():
            global final_result
            return final_result
        '''

        def on_error(ws, error):
            print("Xunfei Websocket Error:")
            print(error)

        def on_close(ws, close_status_code, close_msg):
            # print("\n### websocket closed ###")
            pass

        def on_open(ws, input="你会做什么？", temperature=0.5, max_tokens=1024, top_k=1):
            # print("Connection established")

            if isinstance(input, str):
                messages = [{'role': 'user', 'content': input}]
            else:
                messages = []
                # word_ctr = 0
                # TODO: Implement truncation in PromptList
                for item in input:
                    msg = {'content': item['prompt']}
                    # if word_ctr >= self.max_seq_len:
                    #     break
                    # if len(msg['content']) + word_ctr > self.max_seq_len:
                    #     msg['content'] = msg['content'][word_ctr -
                    #                                     self.max_seq_len:]
                    # word_ctr += len(msg['content'])
                    if item['role'] == 'HUMAN':
                        msg['role'] = 'user'
                    elif item['role'] == 'BOT':
                        msg['role'] = 'assistant'
                    messages.append(msg)
                # in case the word break results in even number of messages
                # if len(messages) > 0 and len(messages) % 2 == 0:
                #     messages = messages[:-1]
            # print('current message is ', messages)
            # 构建要发送的消息
            data = {
                "header": {
                    "traceId": "SPARK_DEMO",
                },
                "parameter": {
                    "chat": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_k": top_k,
                    }
                },
                "payload": {
                    "lora": {"md5": "xxx", "url": "http://xxx"},
                    "message": {
                        "text": messages
                    },
                },
            }

            # 发送消息
            ws.send(json.dumps(data))


        temperature = 0.1
        max_tokens = 4096
        top_k = 1

        # 使用 partial 来传递额外的参数到 on_open 函数
        ws = websocket.WebSocketApp(
            self.path,
            on_open=partial(
                on_open,
                input=input,
                temperature=temperature,
                max_tokens=max_tokens,
                top_k=top_k,
            ),
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        ws.run_forever()

        if final_result[-5:] == '<end>':
            final_result = final_result[:-5]
        print('current final result is: ', final_result)
        return final_result
        # return get_final_result()

if __name__ == '__main__':
    start = time.time()
    # xunfei = XunFei(path="ws://10.80.16.101:9979/turing/v3/gpt")
    xunfei = XunFei(path="ws://10.80.16.101:9989/turing/v3/gpt")
    '''
    print(xunfei.generate(["There is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nThe following excerpt is from a pamphlet.\nYou will do me the justice to remember, that I have always strenuously supported the Right of every man to his own opinion, however different that opinion might be to mine. He who denies to another this right, makes a slave of himself to his present opinion, because he precludes himself the right of changing it.\nThe most formidable weapon against errors of every kind is Reason. I have never used any other, and I trust I never shall.\nThe circumstance that has now taken place in France of the total abolition of the whole national order of priesthood, and of everything appertaining to compulsive systems of religion, and compulsive articles of faith, has not only precipitated my intention, but rendered a work of this kind exceedingly necessary, lest in the general wreck of superstition, of false systems of government, and false theology, we lose sight of morality, of humanity, and of the theology that is true.\nI believe in one God, and no more; and I hope for happiness beyond this life.\nI believe in the equality of man; and I believe that religious duties consist in doing justice, loving mercy, and endeavoring to make our fellow-creatures happy.\nI do not believe in the creed professed by the Jewish church, by the Roman church, by the Greek church, by the Turkish church, by the Protestant church, nor by any church that I know of. My own mind is my own church.\nAll national institutions of churches, whether Jewish, Christian or Turkish, appear to me no other than human inventions, set up to terrify and enslave mankind, and monopolize power and profit.\nI do not mean by this declaration to condemn those who believe otherwise; they have the same right to their belief as I have to mine.\n\u2014Thomas Paine, The Age of Reason, 1794\u20131795\nWhich of the following Enlightenment philosophes designed a system of checks and balances for government to avoid abuses of power?\nA. Jean Jacques Rousseau\nB. Baron Montesquieu\nC. Mary Wollstonecraft\nD. Adam Smith\nAnswer: \nB\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nRead the following excerpt.\nThe revolutionary seed had penetrated into every country and spread more or less. It was greatly developed under the r\u00e9gime of the military despotism of Bonaparte. His conquests displaced a number of laws, institutions, and customs; broke through bonds sacred among all nations, strong enough to resist time itself; which is more than can be said of certain benefits conferred by these innovators.\nThe monarchs will fulfil the duties imposed upon them by Him who, by entrusting them with power, has charged them to watch over the maintenance of justice, and the rights of all, to avoid the paths of error, and tread firmly in the way of truth. Placed beyond the passions which agitate society, it is in days of trial chiefly that they are called upon to despoil realities of their false appearances, and to show themselves as they are, fathers invested with the authority belonging by right to the heads of families, to prove that, in days of mourning, they know how to be just, wise, and therefore strong, and that they will not abandon the people whom they ought to govern to be the sport of factions, to error and its consequences, which must involve the loss of society.\nUnion between the monarchs is the basis of the policy which must now be followed to save society from total ruin. . . .\nLet them not confound concessions made to parties with the good they ought to do for their people, in modifying, according to their recognized needs, such branches of the administration as require it.\nLet them be just, but strong; beneficent, but strict.\nLet them maintain religious principles in all their purity, and not allow the faith to be attacked and morality interpreted according to the social contract or the visions of foolish sectarians.\nLet them suppress Secret Societies; that gangrene of society.\n\u2014Klemens von Metternich, Political Confession of Faith, 1820\nWhich of the following was the greatest cause of the fears expressed by Metternich in the document above?\nA. The ideas of personal liberty and nationalism conceived during the Enlightenment resulted in radical revolutions that could spread throughout Europe.\nB. The conquest of Europe by Napoleon led to the creation of new factions and shifted the European balance of power.\nC. The power of monarchs had grown to the point where it needed to be checked by other powers within each nation or domination of civilians would occur.\nD. The rising and falling economic cycle of the newly emerging capitalist economy could lead to civilian unrest that must be suppressed.\nAnswer: \nA\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nIn Russia there was nothing going on well, and [Souvarine] was in despair over the news he had received. His old companions were all turning to the politicians; the famous Nihilists who made Europe tremble-sons of village priests, of the lower middle class, of tradesmen-could not rise above the idea of national liberation, and seemed to believe that the world would be delivered-when they had killed their despot&\u2026\n\"Foolery! They'll never get out of it with their foolery.\"\nThen, lowering his voice still more, in a few bitter words he described his old dream of fraternity. He had renounced his rank and his fortune; he had gone among workmen, only in the hope of seeing at last the foundation of a new society of labour in common. All the sous in his pockets had long gone to the urchins of the settlement; he had been as tender as a brother with the colliers, smiling at their suspicion, winning them over by his quiet workmanlike ways and his dislike of chattering. But decidedly the fusion had not taken place.\nHis voice changed, his eyes grew bright, he fixed them on \u00e9tienne, directly addressing him:\n\"Now, do you understand that? These hatworkers at Marseilles who have won the great lottery prize of a hundred thousand francs have gone off at once and invested it, declaring that they are going to live without doing anything! Yes, that is your idea, all of you French workmen; you want to unearth a treasure in order to devour it alone afterwards in some lazy, selfish corner. You may cry out as much as you like against the rich, you haven't got courage enough to give back to the poor the money that luck brings you. You will never be worthy of happiness as long as you own anything, and your hatred of the bourgeois proceeds solely from an angry desire to be bourgeois yourselves in their place.\"\n\u00e9mile Zola, French writer, Germinal, 1885\nThe passage displays the direct concern for the welfare of the working classes that was typically a part of which movement?\nA. Capitalist\nB. Scientific\nC. Communist\nD. Existentialist\nAnswer: \nC\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nThe excerpts below are from the Navigation Acts of 1651.\n[A]fter the first day of December, one thousand six hundred fifty and one, and from thence forwards, no goods or commodities whatsoever of the growth, production or manufacture of Asia, Africa or America, or of any part thereof; or of any islands belonging to them, or which are described or laid down in the usual maps or cards of those places, as well of the English plantations as others, shall be imported or brought into this Commonwealth of England, or into Ireland, or any other lands, islands, plantations, or territories to this Commonwealth belonging, or in their possession, in any other ship or ships, vessel or vessels whatsoever, but only in such as do truly and without fraud belong only to the people of this Commonwealth, or the plantations thereof, as the proprietors or right owners thereof; and whereof the master and mariners are also of the people of this Commonwealth, under the penalty of the forfeiture and loss of all the goods that shall be imported contrary to this act, , , ,\n[N]o goods or commodities of the growth, production, or manufacture of Europe, or of any part thereof, shall after the first day of December, one thousand six hundred fifty and one, be imported or brought into this Commonwealth of England, or any other lands or territories to this Commonwealth belonging, or in their possession, in any ship or ships, vessel or vessels whatsoever, but in such as do truly and without fraud belong only to the people of this Commonwealth, and in no other, except only such foreign ships and vessels as do truly and properly belong to the people of that country or place, of which the said goods are the growth, production or manufacture.\nWhich of the following best describes the outcome of the Navigation Acts of 1651?\nA. They served as a catalyst for the growth of English shipping and overseas trade, but did little to limit the prospects of the Dutch in the seventeenth century.\nB. They brought about almost immediate hardships for the Dutch economy as their dominance of overseas trade quickly ended.\nC. They were rescinded during the restoration of the Stuarts as they sought normal diplomatic relations with the Dutch so not as to need Parliament's financial support for war.\nD. They led to nearly a century of recurrent war between England and the Netherlands, which would not end until after American independence.\nAnswer: \nA\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nAlbeit the king's Majesty justly and rightfully is and ought to be the supreme head of the Church of England, and so is recognized by the clergy of this realm in their convocations, yet nevertheless, for corroboration and confirmation thereof, and for increase of virtue in Christ's religion within this realm of England, and to repress and extirpate all errors, heresies, and other enormities and abuses heretofore used in the same, be it enacted, by authority of this present Parliament, that the king, our sovereign lord, his heirs and successors, kings of this realm, shall be taken, accepted, and reputed the only supreme head in earth of the Church of England, called Anglicans Ecclesia; and shall have and enjoy, annexed and united to the imperial crown of this realm, as well the title and style thereof, as all honors, dignities, preeminences, jurisdictions, privileges, authorities, immunities, profits, and commodities to the said dignity of the supreme head of the same Church belonging and appertaining; and that our said sovereign lord, his heirs and successors, kings of this realm, shall have full power and authority from time to time to visit, repress, redress, record, order, correct, restrain, and amend all such errors, heresies, abuses, offenses, contempts, and enormities, whatsoever they be, which by any manner of spiritual authority or jurisdiction ought or may lawfully be reformed, repressed, ordered, redressed, corrected, restrained, or amended, most to the pleasure of Almighty God, the increase of virtue in Christ's religion, and for the conservation of the peace, unity, and tranquility of this realm; any usage, foreign land, foreign authority, prescription, or any other thing or things to the contrary hereof notwithstanding.\nEnglish Parliament, Act of Supremacy, 1534\nFrom the passage, one may infer that the English Parliament wished to argue that the Act of Supremacy would\nA. give the English king a new position of authority\nB. give the position of head of the Church of England to Henry VIII alone and exclude his heirs\nC. establish Calvinism as the one true theology in England\nD. end various forms of corruption plaguing the Church in England\nAnswer: \nD\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nIn order to make the title of this discourse generally intelligible, I have translated the term \"Protoplasm,\" which is the scientific name of the substance of which I am about to speak, by the words \"the physical basis of life.\" I suppose that, to many, the idea that there is such a thing as a physical basis, or matter, of life may be novel\u2014so widely spread is the conception of life as something which works through matter. \u2026 Thus the matter of life, so far as we know it (and we have no right to speculate on any other), breaks up, in consequence of that continual death which is the condition of its manifesting vitality, into carbonic acid, water, and nitrogenous compounds, which certainly possess no properties but those of ordinary matter.\nThomas Henry Huxley, \"The Physical Basis of Life,\" 1868\nFrom the passage, one may infer that Huxley argued that \"life\" was\nA. a force that works through matter\nB. essentially a philosophical notion\nC. merely a property of a certain kind of matter\nD. a supernatural phenomenon\nAnswer: ",
                           "Follow the given examples and answer the question.\nName geometric shapes from their SVG paths.\n\nQ: This SVG path element <path d=\"M 31.00,73.00 L 32.00,59.00 L 44.00,50.00 L 49.00,41.00 L 64.00,37.00 L 71.00,55.00 L 64.00,76.00 L 52.00,61.00 L 31.00,73.00\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 9 separate commands.\n(1) M 31.00,73.00: Move the current point to 31.00,73.00.\n(2) L 32.00,59.00: Create a line from 31.00,73.00 to 32.00,59.00.\n(3) L 44.00,50.00: Create a line from 32.00,59.00 to 44.00,50.00.\n(4) L 49.00,41.00: Create a line from 44.00,50.00 to 49.00,41.00.\n(5) L 64.00,37.00: Create a line from 49.00,41.00 to 64.00,37.00.\n(6) L 71.00,55.00: Create a line from 64.00,37.00 to 71.00,55.00.\n(7) L 64.00,76.00: Create a line from 71.00,55.00 to 64.00,76.00.\n(8) L 52.00,61.00: Create a line from 64.00,76.00 to 52.00,61.00.\n(9) L 31.00,73.00: Create a line from 52.00,61.00 to 31.00,73.00.\nThis SVG path starts at point 31.00,73.00, creates eight consecutive and touching lines, and then returns back its starting point, thereby creating an eight-sided shape. It does not have any curves or arches. \"octagon\" is the only eight-sided object on the list. So the answer is (F).\n\nQ: This SVG path element <path d=\"M 14.19,26.04 L 51.43,39.21 L 58.44,36.69 L 56.63,30.17 L 48.53,26.66 L 14.19,26.04\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 6 separate commands.\n(1) M 14.19,26.04: Move the current point to 14.19,26.04.\n(2) L 51.43,39.21: Create a line from 14.19,26.04 to 51.43,39.21.\n(3) L 58.44,36.69: Create a line from 51.43,39.21 to 58.44,36.69.\n(4) L 56.63,30.17: Create a line from 58.44,36.69 to 56.63,30.17.\n(5) L 48.53,26.66: Create a line from 56.63,30.17 to 48.53,26.66.\n(6) L 14.19,26.04: Create a line from 48.53,26.66 to 14.19,26.04.\nThis SVG path starts at point 14.19,26.04, creates five consecutive and touching lines, and then returns back its starting point, thereby creating a five-sided shape. It does not have any curves or arches. \"pentagon\" is the only five-sided polygon on the list. So the answer is (G).\n\nQ: This SVG path element <path d=\"M 41.00,43.00 L 37.00,34.00 L 41.00,33.00 L 45.00,34.00 L 41.00,43.00\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.\nThis SVG path element contains \"M\" and \"L\" commands. M takes two parameters (x,y) and moves the current point to the coordinates (x,y). L takes two parameters (x,y) and draws a line from the previous coordinate to the new coordinate (x,y).\nThis path can be decomposed into 5 separate commands.\n(1) M 41.00,43.00: Move the current point to 41.00,43.00.\n(2) L 37.00,34.00: Create a line from 41.00,43.00 to 37.00,34.00.\n(3) L 41.00,33.00: Create a line from 37.00,34.00 to 41.00,33.00.\n(4) L 45.00,34.00: Create a line from 41.00,33.00 to 45.00,34.00.\n(5) L 41.00,43.00: Create a line from 45.00,34.00 to 41.00,43.00.\nThis SVG path starts at point 41.00,43.00, creates four consecutive and touching lines, and then returns back its starting point, thereby creating a four-sided shape. \"kite\" and \"rectangle\" are the only two four-sided polygons on the list. So, we need to determine which one is the correct answer.\nA kite has two pairs of equal-length adjacent sides, whereas a rectangle has two pairs of equal-length alternate (opposite) sides. Now, let's check whether the two adjacent sides of this shape are equal.\nLength of side A: |A| = sqrt((41.00-37.00)^2 + (43.00-34.00)^2) = sqrt((4)^2 + (9)^2) = sqrt(16 + 81) = sqrt(97).\nLength of side B: |B| = sqrt((37.00-41.00)^2 + (34.00-33.00)^2)) = sqrt((4)^2 + (1)^2) = sqrt(16 + 1) = sqrt(17).\nLength of side C: |C| = sqrt((41.00-45.00)^2 + (33.00-34.00)^2)) = sqrt((-4)^2 + (-1)^2) = sqrt(16 + 1) = sqrt(17).\nLength of side D: |D| = sqrt((45.00-41.00)^2 + (34.00-43.00)^2)) = sqrt((4)^2 + (-9)^2) = sqrt(16 + 81) = sqrt(97).\nNote that |A| = |D| and |B| = |C|. Furthermore, A and D are adjacent and B and C are adjacent. Thus, this polygon has two pairs of equal-length adjacent sides and is \"kite\". So the answer is (D).\n\nQ: This SVG path element <path d=\"M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L 45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69\"/> draws a\nOptions:\n(A) circle\n(B) heptagon\n(C) hexagon\n(D) kite\n(E) line\n(F) octagon\n(G) pentagon\n(H) rectangle\n(I) sector\n(J) triangle\nA: Let's think step by step.",
                           "Question: Angelo and Melanie want to plan how many hours over the next week they should study together for their test next week. They have 2 chapters of their textbook to study and 4 worksheets to memorize. They figure out that they should dedicate 3 hours to each chapter of their textbook and 1.5 hours for each worksheet. If they plan to study no more than 4 hours each day, how many days should they plan to study total over the next week if they take a 10-minute break every hour, include 3 10-minute snack breaks each day, and 30 minutes for lunch each day?\nLet's think step by step\nAnswer:\nAngelo and Melanie think they should dedicate 3 hours to each of the 2 chapters, 3 hours x 2 chapters = 6 hours total.\nFor the worksheets they plan to dedicate 1.5 hours for each worksheet, 1.5 hours x 4 worksheets = 6 hours total.\nAngelo and Melanie need to start with planning 12 hours to study, at 4 hours a day, 12 / 4 = 3 days.\nHowever, they need to include time for breaks and lunch. Every hour they want to include a 10-minute break, so 12 total hours x 10 minutes = 120 extra minutes for breaks.\nThey also want to include 3 10-minute snack breaks, 3 x 10 minutes = 30 minutes.\nAnd they want to include 30 minutes for lunch each day, so 120 minutes for breaks + 30 minutes for snack breaks + 30 minutes for lunch = 180 minutes, or 180 / 60 minutes per hour = 3 extra hours.\nSo Angelo and Melanie want to plan 12 hours to study + 3 hours of breaks = 15 hours total.\nThey want to study no more than 4 hours each day, 15 hours / 4 hours each day = 3.75\nThey will need to plan to study 4 days to allow for all the time they need.\nThe answer is 4\n\nQuestion: Mark's basketball team scores 25 2 pointers, 8 3 pointers and 10 free throws.  Their opponents score double the 2 pointers but half the 3 pointers and free throws.  What's the total number of points scored by both teams added together?\nLet's think step by step\nAnswer:\nMark's team scores 25 2 pointers, meaning they scored 25*2= 50 points in 2 pointers.\nHis team also scores 6 3 pointers, meaning they scored 8*3= 24 points in 3 pointers\nThey scored 10 free throws, and free throws count as one point so they scored 10*1=10 points in free throws.\nAll together his team scored 50+24+10= 84 points\nMark's opponents scored double his team's number of 2 pointers, meaning they scored 50*2=100 points in 2 pointers.\nHis opponents scored half his team's number of 3 pointers, meaning they scored 24/2= 12 points in 3 pointers.\nThey also scored half Mark's team's points in free throws, meaning they scored 10/2=5 points in free throws.\nAll together Mark's opponents scored 100+12+5=117 points\nThe total score for the game is both team's scores added together, so it is 84+117=201 points\nThe answer is 201\n\nQuestion: Bella has two times as many marbles as frisbees. She also has 20 more frisbees than deck cards. If she buys 2/5 times more of each item, what would be the total number of the items she will have if she currently has 60 marbles?\nLet's think step by step\nAnswer:\nWhen Bella buys 2/5 times more marbles, she'll have increased the number of marbles by 2/5*60 = 24\nThe total number of marbles she'll have is 60+24 = 84\nIf Bella currently has 60 marbles, and she has two times as many marbles as frisbees, she has 60/2 = 30 frisbees.\nIf Bella buys 2/5 times more frisbees, she'll have 2/5*30 = 12 more frisbees.\nThe total number of frisbees she'll have will increase to 30+12 = 42\nBella also has 20 more frisbees than deck cards, meaning she has 30-20 = 10 deck cards\nIf she buys 2/5 times more deck cards, she'll have 2/5*10 = 4 more deck cards.\nThe total number of deck cards she'll have is 10+4 = 14\nTogether, Bella will have a total of 14+42+84 = 140 items\nThe answer is 140\n\nQuestion: A group of 4 fruit baskets contains 9 apples, 15 oranges, and 14 bananas in the first three baskets and 2 less of each fruit in the fourth basket. How many fruits are there?\nLet's think step by step\nAnswer:\nFor the first three baskets, the number of apples and oranges in one basket is 9+15=24\nIn total, together with bananas, the number of fruits in one basket is 24+14=38 for the first three baskets.\nSince there are three baskets each having 38 fruits, there are 3*38=114 fruits in the first three baskets.\nThe number of apples in the fourth basket is 9-2=7\nThere are also 15-2=13 oranges in the fourth basket\nThe combined number of oranges and apples in the fourth basket is 13+7=20\nThe fourth basket also contains 14-2=12 bananas.\nIn total, the fourth basket has 20+12=32 fruits.\nThe four baskets together have 32+114=146 fruits.\nThe answer is 146\n\nQuestion: Bruce works for 5 hours on Tuesday. On Wednesday he works twice the time he works on Tuesday. On Thursday he works 2 hours less than the time he works on Wednesday. How many hours does Bruce work in all these three days?\nLet's think step by step\nAnswer:"]))
    '''
    print(xunfei._generate("以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\nUnix的推测文件的类型的命令是____。\nA. file\nB. diff\nC. ls –l\nD. type\n答案: \nA\n以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\n用户编写的C程序中的自动变量位于进程映像的____部分。\nA. 数据段\nB. 用户栈\nC. 正文段\nD. 堆段\n答案: \nB\n以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\n请求分页存储管理系统的基础是程序运行的____原理。\nA. 动态性\nB. 局部性\nC. 全局性\nD. 虚拟性\n答案: \nB\n以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\nUnix操作系统在中断处理返回后，将____。\nA. 选择刚被中断的进程执行\nB. 选择就绪队列中的一个进程执行\nC. 等待下—个中断的发生\nD. 按预定策略选择进程执行\n答案: \nD\n以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\n如有多个中断同时发生，要影响和调整中断事件的响应次序，可以利用____。\nA. 中断向量\nB. 中断嵌套\nC. 中断优先级\nD. 中断屏蔽\n答案: \nD\n以下是中国关于操作系统考试的单项选择题，请选出其中的正确答案。\n下面几条中，____是动态重定位的特点。\nA. 需要一个复杂的重定位装入程序\nB. 存储管理算法比较简单\nC. 不需地址变换硬件机构的支持\nD. 在执行时将逻辑地址变换成内存地址\n答案: "))
    # print(xunfei._generate('你是谁'))
    end = time.time()
    print('Xunfei local time cost ', end - start)